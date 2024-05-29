from functools import partial
from itertools import count
from json import loads
from logging import getLogger
from math import inf
from typing import Callable, Sequence

from packit.agent import Agent
from packit.conditions import condition_or, condition_threshold
from packit.loops import loop_retry
from packit.results import function_result
from packit.toolbox import Toolbox
from packit.utils import could_be_json

from taleweave.actions.base import (
    action_ask,
    action_examine,
    action_give,
    action_move,
    action_take,
    action_tell,
)
from taleweave.actions.planning import (
    check_calendar,
    erase_notes,
    get_recent_notes,
    read_notes,
    replace_note,
    schedule_event,
    summarize_notes,
    take_note,
)
from taleweave.context import (
    broadcast,
    get_character_agent_for_name,
    get_character_for_agent,
    get_current_turn,
    get_current_world,
    set_current_character,
    set_current_room,
    set_current_turn,
    set_current_world,
    set_game_systems,
)
from taleweave.game_system import GameSystem
from taleweave.models.config import DEFAULT_CONFIG
from taleweave.models.entity import Character, Room, World
from taleweave.models.event import ActionEvent, ResultEvent
from taleweave.utils.conversation import make_keyword_condition, summarize_room
from taleweave.utils.effect import expire_effects
from taleweave.utils.planning import expire_events, get_upcoming_events
from taleweave.utils.search import find_containing_room
from taleweave.utils.world import describe_entity, format_attributes

logger = getLogger(__name__)


turn_config = DEFAULT_CONFIG.world.turn


def world_result_parser(value, agent, **kwargs):
    current_world = get_current_world()
    if not current_world:
        raise ValueError(
            "The current world must be set before calling world_result_parser"
        )

    logger.debug(f"parsing action for {agent.name}: {value}")

    current_character = get_character_for_agent(agent)
    current_room = next(
        (room for room in current_world.rooms if current_character in room.characters),
        None,
    )

    set_current_room(current_room)
    set_current_character(current_character)

    return function_result(value, agent=agent, **kwargs)


def prompt_character_action(
    room, character, agent, action_names, action_toolbox, current_turn
) -> str:
    # collect data for the prompt
    notes_prompt, events_prompt = get_notes_events(character, current_turn)

    room_characters = [character.name for character in room.characters]
    room_items = [item.name for item in room.items]
    room_directions = [portal.name for portal in room.portals]

    character_attributes = format_attributes(character)
    # character_effects = [effect.name for effect in character.active_effects]
    character_items = [item.name for item in character.items]

    # set up a result parser for the agent
    def result_parser(value, **kwargs):
        if not room or not character:
            raise ValueError("Room and character must be set before parsing results")

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
            event = ActionEvent.from_json(value, room, character)
        else:
            # TODO: this should be removed and throw
            event = ResultEvent(value, room, character)

        broadcast(event)

        return world_result_parser(value, **kwargs)

    # prompt and act
    logger.info("starting turn for character: %s", character.name)
    result = loop_retry(
        agent,
        (
            "You are currently in the {room_name} room. {room_description}. {attributes}. "
            "The room contains the following characters: {visible_characters}. "
            "The room contains the following items: {visible_items}. "
            "Your inventory contains the following items: {character_items}."
            "You can take the following actions: {actions}. "
            "You can move in the following directions: {directions}. "
            "{notes_prompt} {events_prompt}"
            "What will you do next? Reply with a JSON function call, calling one of the actions."
            "You can only perform one action per turn. What is your next action?"
        ),
        context={
            "actions": action_names,
            "character_items": character_items,
            "attributes": character_attributes,
            "directions": room_directions,
            "room_name": room.name,
            "room_description": describe_entity(room),
            "visible_characters": room_characters,
            "visible_items": room_items,
            "notes_prompt": notes_prompt,
            "events_prompt": events_prompt,
        },
        result_parser=result_parser,
        toolbox=action_toolbox,
    )

    logger.debug(f"{character.name} action result: {result}")
    if agent.memory:
        # TODO: make sure this is not duplicating memories and wasting space
        agent.memory.append(result)

    return result


def get_notes_events(character: Character, current_turn: int):
    recent_notes = get_recent_notes(character)
    upcoming_events = get_upcoming_events(character, current_turn)

    if len(recent_notes) > 0:
        notes = "\n".join(recent_notes)
        notes_prompt = f"Your recent notes are: {notes}\n"
    else:
        notes_prompt = "You have no recent notes.\n"

    if len(upcoming_events) > 0:
        current_turn = get_current_turn()
        events = [
            f"{event.name} in {event.turn - current_turn} turns"
            for event in upcoming_events
        ]
        events = "\n".join(events)
        events_prompt = f"Upcoming events are: {events}\n"
    else:
        events_prompt = "You have no upcoming events.\n"

    return notes_prompt, events_prompt


def prompt_character_think(
    room: Room,
    character: Character,
    agent: Agent,
    planner_toolbox: Toolbox,
    current_turn: int,
    max_steps: int | None = None,
) -> str:
    max_steps = max_steps or turn_config.planning_steps

    notes_prompt, events_prompt = get_notes_events(character, current_turn)

    event_count = len(character.planner.calendar.events)
    note_count = len(character.planner.notes)

    logger.info("starting planning for character: %s", character.name)
    _, condition_end, result_parser = make_keyword_condition("You are done planning.")
    stop_condition = condition_or(
        condition_end, partial(condition_threshold, max=max_steps)
    )

    i = 0
    while not stop_condition(current=i):
        result = loop_retry(
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
                "room_summary": summarize_room(room, character),
            },
            result_parser=result_parser,
            stop_condition=stop_condition,
            toolbox=planner_toolbox,
        )

        if agent.memory:
            agent.memory.append(result)

        i += 1

    return result


def simulate_world(
    world: World,
    turns: float | int = inf,
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
            action_examine,
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
            check_calendar,
            erase_notes,
            read_notes,
            replace_note,
            schedule_event,
            summarize_notes,
            take_note,
        ]
    )

    # simulate each character
    for i in count():
        current_turn = get_current_turn()
        logger.info(f"simulating turn {i} of {turns} (world turn {current_turn})")

        for character_name in world.order:
            character, agent = get_character_agent_for_name(character_name)
            if not agent or not character:
                logger.error(f"agent or character not found for name {character_name}")
                continue

            room = find_containing_room(world, character)
            if not room:
                logger.error(f"character {character_name} is not in a room")
                continue

            # prep context
            set_current_room(room)
            set_current_character(character)

            # decrement effects on the character and remove any that have expired
            expire_effects(character)
            expire_events(character, current_turn)

            # give the character a chance to think and check their planner
            if agent.memory and len(agent.memory) > 0:
                try:
                    thoughts = prompt_character_think(
                        room, character, agent, planner_toolbox, current_turn
                    )
                    logger.debug(f"{character.name} thinks: {thoughts}")
                except Exception:
                    logger.exception(
                        f"error during planning for character {character.name}"
                    )

            try:
                result = prompt_character_action(
                    room, character, agent, action_names, action_tools, current_turn
                )
                result_event = ResultEvent(
                    result=result, room=room, character=character
                )
                broadcast(result_event)
            except Exception:
                logger.exception(f"error during action for character {character.name}")

        for system in systems:
            if system.simulate:
                system.simulate(world, current_turn)

        set_current_turn(current_turn + 1)
        if i >= turns:
            logger.info("reached turn limit at world turn %s", current_turn + 1)
            break
