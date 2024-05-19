from itertools import count
from logging import getLogger
from math import inf
from typing import Callable, Sequence

from packit.loops import loop_retry
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
from adventure.models.entity import World
from adventure.models.event import ActionEvent, ReplyEvent, ResultEvent
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


def simulate_world(
    world: World,
    steps: float | int = inf,
    actions: Sequence[Callable[..., str]] = [],
    systems: Sequence[GameSystem] = [],
):
    logger.info("Simulating the world")
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

    # simulate each actor
    for i in count():
        current_step = get_current_step()
        logger.info(f"simulating step {i} of {steps} (world step {current_step})")

        for actor_name in world.order:
            actor, agent = get_actor_agent_for_name(actor_name)
            if not agent or not actor:
                logger.error(f"Agent or actor not found for name {actor_name}")
                continue

            room = find_room_with_actor(world, actor)
            if not room:
                logger.error(f"Actor {actor_name} is not in a room")
                continue

            room_actors = [actor.name for actor in room.actors]
            room_items = [item.name for item in room.items]
            room_directions = [portal.name for portal in room.portals]

            actor_attributes = format_attributes(actor)
            actor_items = [item.name for item in actor.items]

            def result_parser(value, agent, **kwargs):
                if not room or not actor:
                    raise ValueError(
                        "Room and actor must be set before parsing results"
                    )

                if could_be_json(value):
                    event = ActionEvent.from_json(value, room, actor)
                else:
                    event = ReplyEvent.from_text(value, room, actor)

                broadcast(event)

                return world_result_parser(value, agent, **kwargs)

            logger.info("starting turn for actor: %s", actor_name)
            result = loop_retry(
                agent,
                (
                    "You are currently in {room_name}. {room_description}. {attributes}. "
                    "The room contains the following characters: {visible_actors}. "
                    "The room contains the following items: {visible_items}. "
                    "Your inventory contains the following items: {actor_items}."
                    "You can take the following actions: {actions}. "
                    "You can move in the following directions: {directions}. "
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
                },
                result_parser=result_parser,
                toolbox=action_tools,
            )

            logger.debug(f"{actor.name} step result: {result}")
            if agent.memory:
                agent.memory.append(result)

            result_event = ResultEvent(result=result, room=room, actor=actor)
            broadcast(result_event)

        for system in systems:
            if system.simulate:
                system.simulate(world, current_step)

        set_current_step(current_step + 1)
        if i > steps:
            logger.info("reached step limit at world step %s", current_step + 1)
            break
