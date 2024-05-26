from functools import partial
from itertools import count
from json import loads
from logging import getLogger
from math import inf
from typing import Callable, Sequence

from packit.agent import Agent
from packit.conditions import condition_or, condition_threshold
from packit.loops import loop_reduce, loop_retry
from packit.results import multi_function_or_str_result
from packit.toolbox import Toolbox
from packit.utils import could_be_json

from adventure.actions.base import (
    action_ask,
    action_give,
    action_look,
    action_move,
    action_take,
    action_tell,
)
from adventure.actions.planning import (
    check_calendar,
    erase_notes,
    get_recent_notes,
    read_notes,
    replace_note,
    schedule_event,
    take_note,
)
from adventure.context import (
    broadcast,
    get_actor_agent_for_name,
    get_actor_for_agent,
    get_current_step,
    get_current_world,
    set_current_actor,
    set_current_room,
    set_current_step,
    set_current_world,
    set_game_systems,
)
from adventure.game_system import GameSystem
from adventure.models.entity import Actor, Room, World
from adventure.models.event import ActionEvent, ReplyEvent, ResultEvent
from adventure.utils.conversation import make_keyword_condition, summarize_room
from adventure.utils.effect import expire_effects
from adventure.utils.planning import expire_events, get_upcoming_events
from adventure.utils.search import find_room_with_actor
from adventure.utils.world import describe_entity, format_attributes

logger = getLogger(__name__)


def world_result_parser(value, agent, **kwargs):
    current_world = get_current_world()
    if not current_world:
        raise ValueError(
            "The current world must be set before calling world_result_parser"
        )

    logger.debug(f"parsing action for {agent.name}: {value}")

    current_actor = get_actor_for_agent(agent)
    current_room = next(
        (room for room in current_world.rooms if current_actor in room.actors), None
    )

    set_current_room(current_room)
    set_current_actor(current_actor)

    return multi_function_or_str_result(value, agent=agent, **kwargs)


def prompt_actor_action(
    room, actor, agent, action_names, action_toolbox, current_turn
) -> str:
    # collect data for the prompt
    notes_prompt, events_prompt = get_notes_events(actor, current_turn)

    room_actors = [actor.name for actor in room.actors]
    room_items = [item.name for item in room.items]
    room_directions = [portal.name for portal in room.portals]

    actor_attributes = format_attributes(actor)
    # actor_effects = [effect.name for effect in actor.active_effects]
    actor_items = [item.name for item in actor.items]

    # set up a result parser for the agent
    def result_parser(value, agent, **kwargs):
        if not room or not actor:
            raise ValueError("Room and actor must be set before parsing results")

        # trim suffixes that are used elsewhere
        value = value.removesuffix("END").strip()

        # fix unbalanced curly braces
        if value.startswith("{") and not value.endswith("}"):
            open_count = value.count("{")
            close_count = value.count("}")

            if open_count > close_count:
                fixed_value = value + ("}" * (open_count - close_count))
                try:
                    loads(fixed_value)
                    value = fixed_value
                except Exception:
                    pass

        if could_be_json(value):
            event = ActionEvent.from_json(value, room, actor)
        else:
            event = ReplyEvent.from_text(value, room, actor)

        broadcast(event)

        return world_result_parser(value, agent, **kwargs)

    # prompt and act
    logger.info("starting turn for actor: %s", actor.name)
    result = loop_retry(
        agent,
        (
            "You are currently in the {room_name} room. {room_description}. {attributes}. "
            "The room contains the following characters: {visible_actors}. "
            "The room contains the following items: {visible_items}. "
            "Your inventory contains the following items: {actor_items}."
            "You can take the following actions: {actions}. "
            "You can move in the following directions: {directions}. "
            "{notes_prompt} {events_prompt}"
            "What will you do next? Reply with a JSON function call, calling one of the actions."
            "You can only perform one action per turn. What is your next action?"
        ),
        context={
            "actions": action_names,
            "actor_items": actor_items,
            "attributes": actor_attributes,
            "directions": room_directions,
            "room_name": room.name,
            "room_description": describe_entity(room),
            "visible_actors": room_actors,
            "visible_items": room_items,
            "notes_prompt": notes_prompt,
            "events_prompt": events_prompt,
        },
        result_parser=result_parser,
        toolbox=action_toolbox,
    )

    logger.debug(f"{actor.name} step result: {result}")
    if agent.memory:
        # TODO: make sure this is not duplicating memories and wasting space
        agent.memory.append(result)

    return result


def get_notes_events(actor: Actor, current_turn: int):
    recent_notes = get_recent_notes(actor)
    upcoming_events = get_upcoming_events(actor, current_turn)

    if len(recent_notes) > 0:
        notes = "\n".join(recent_notes)
        notes_prompt = f"Your recent notes are: {notes}\n"
    else:
        notes_prompt = "You have no recent notes.\n"

    if len(upcoming_events) > 0:
        current_step = get_current_step()
        events = [
            f"{event.name} in {event.turn - current_step} turns"
            for event in upcoming_events
        ]
        events = "\n".join(events)
        events_prompt = f"Upcoming events are: {events}\n"
    else:
        events_prompt = "You have no upcoming events.\n"

    return notes_prompt, events_prompt


def prompt_actor_think(
    room: Room, actor: Actor, agent: Agent, planner_toolbox: Toolbox, current_turn: int
) -> str:
    notes_prompt, events_prompt = get_notes_events(actor, current_turn)

    event_count = len(actor.planner.calendar.events)
    note_count = len(actor.planner.notes)

    logger.info("starting planning for actor: %s", actor.name)
    _, condition_end, result_parser = make_keyword_condition("You are done planning.")
    stop_condition = condition_or(condition_end, partial(condition_threshold, max=3))

    result = loop_reduce(
        agent,
        "You are about to start your turn. Plan your next action carefully. Take notes and schedule events to help keep track of your goals. "
        "You can check your notes for important facts or check your calendar for upcoming events. You have {note_count} notes. "
        "If you have plans with other characters, schedule them on your calendar. You have {event_count} events on your calendar. "
        "{room_summary}"
        "Think about your goals and any quests that you are working on, and plan your next action accordingly. "
        "Try to keep your notes accurate and up-to-date. Replace or erase old notes when they are no longer accurate or useful. "
        "Do not keeps notes about upcoming events, use your calendar for that. "
        "You can perform up to 3 planning actions in a single turn. When you are done planning, reply with 'END'."
        "{notes_prompt} {events_prompt}",
        context={
            "event_count": event_count,
            "events_prompt": events_prompt,
            "note_count": note_count,
            "notes_prompt": notes_prompt,
            "room_summary": summarize_room(room, actor),
        },
        result_parser=result_parser,
        stop_condition=stop_condition,
        toolbox=planner_toolbox,
    )

    if agent.memory:
        agent.memory.append(result)

    return result


def simulate_world(
    world: World,
    steps: float | int = inf,
    actions: Sequence[Callable[..., str]] = [],
    systems: Sequence[GameSystem] = [],
):
    logger.info("simulating the world")
    set_current_world(world)
    set_game_systems(systems)

    # build a toolbox for the actions
    action_tools = Toolbox(
        [
            action_ask,
            action_give,
            action_look,
            action_move,
            action_take,
            action_tell,
            *actions,
        ]
    )
    action_names = action_tools.list_tools()

    # build a toolbox for the planners
    planner_toolbox = Toolbox(
        [
            take_note,
            read_notes,
            replace_note,
            erase_notes,
            schedule_event,
            check_calendar,
        ]
    )

    # simulate each actor
    for i in count():
        current_step = get_current_step()
        logger.info(f"simulating step {i} of {steps} (world step {current_step})")

        for actor_name in world.order:
            actor, agent = get_actor_agent_for_name(actor_name)
            if not agent or not actor:
                logger.error(f"agent or actor not found for name {actor_name}")
                continue

            room = find_room_with_actor(world, actor)
            if not room:
                logger.error(f"actor {actor_name} is not in a room")
                continue

            # prep context
            set_current_room(room)
            set_current_actor(actor)

            # decrement effects on the actor and remove any that have expired
            expire_effects(actor)
            expire_events(actor, current_step)

            # give the actor a chance to think and check their planner
            if agent.memory and len(agent.memory) > 0:
                try:
                    thoughts = prompt_actor_think(
                        room, actor, agent, planner_toolbox, current_step
                    )
                    logger.debug(f"{actor.name} thinks: {thoughts}")
                except Exception:
                    logger.exception(f"error during planning for actor {actor.name}")

            result = prompt_actor_action(
                room, actor, agent, action_names, action_tools, current_step
            )
            result_event = ResultEvent(result=result, room=room, actor=actor)
            broadcast(result_event)

        for system in systems:
            if system.simulate:
                system.simulate(world, current_step)

        set_current_step(current_step + 1)
        if i >= steps:
            logger.info("reached step limit at world step %s", current_step + 1)
            break
