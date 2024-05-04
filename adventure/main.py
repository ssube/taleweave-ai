from importlib import import_module
from json import load
from os import environ, path
from typing import Callable, Dict, Sequence, Tuple

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.loops import loop_retry
from packit.results import multi_function_or_str_result
from packit.toolbox import Toolbox
from packit.utils import logger_with_colors

from adventure.actions import (
    action_ask,
    action_give,
    action_look,
    action_move,
    action_take,
    action_tell,
)
from adventure.context import (
    get_actor_agent_for_name,
    get_actor_for_agent,
    get_current_world,
    get_step,
    set_current_actor,
    set_current_room,
    set_current_world,
    set_step,
)
from adventure.generate import generate_world
from adventure.models import Actor, Room, World, WorldState
from adventure.state import create_agents, save_world, save_world_state

logger = logger_with_colors(__name__)

load_dotenv(environ.get("ADVENTURE_ENV", ".env"), override=True)


# simulation
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
    steps: int = 10,
    actions: Sequence[Callable[..., str]] = [],
    systems: Sequence[
        Tuple[Callable[[World, int], None], Callable[[Dict[str, str]], str] | None]
    ] = [],
    input_callbacks: Sequence[Callable[[Room, Actor, str], None]] = [],
    result_callbacks: Sequence[Callable[[Room, Actor, str], None]] = [],
):
    logger.info("Simulating the world")
    set_current_world(world)

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
    for i in range(steps):
        current_step = get_step()
        logger.info(f"Simulating step {current_step}")
        for actor_name in world.order:
            actor, agent = get_actor_agent_for_name(actor_name)
            if not agent or not actor:
                logger.error(f"Agent or actor not found for name {actor_name}")
                continue

            room = next((room for room in world.rooms if actor in room.actors), None)
            if not room:
                logger.error(f"Actor {actor_name} is not in a room")
                continue

            room_actors = [actor.name for actor in room.actors]
            room_items = [item.name for item in room.items]
            room_directions = list(room.portals.keys())

            actor_attributes = " ".join(
                system_format(actor.attributes)
                for _, system_format in systems
                if system_format
            )
            actor_items = [item.name for item in actor.items]

            def result_parser(value, agent, **kwargs):
                for callback in input_callbacks:
                    callback(room, actor, value)

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
                    "You can only take one action per turn. Pick the most important action and save the rest for later."
                    "What is your action?"
                ),
                context={
                    "actions": action_names,
                    "actor_items": actor_items,
                    "attributes": actor_attributes,
                    "directions": room_directions,
                    "room_name": room.name,
                    "room_description": room.description,
                    "visible_actors": room_actors,
                    "visible_items": room_items,
                },
                result_parser=result_parser,
                toolbox=action_tools,
            )

            logger.debug(f"{actor.name} step result: {result}")
            agent.memory.append(result)

            for callback in result_callbacks:
                callback(room, actor, result)

        for system_update, _ in systems:
            system_update(world, current_step)

        set_step(current_step + 1)


# main
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and simulate a text adventure world"
    )
    parser.add_argument(
        "--actions",
        type=str,
        nargs="*",
        help="Extra actions to include in the simulation",
    )
    parser.add_argument(
        "--flavor", type=str, help="Some additional flavor text for the generated world"
    )
    parser.add_argument(
        "--player", type=str, help="The name of the character to play as"
    )
    parser.add_argument(
        "--rooms", type=int, default=5, help="The number of rooms to generate"
    )
    parser.add_argument(
        "--max-rooms", type=int, help="The maximum number of rooms to generate"
    )
    parser.add_argument(
        "--server", type=str, help="The address on which to run the server"
    )
    parser.add_argument(
        "--state",
        type=str,
        # default="world.state.json",
        help="The file to save the world state to. Defaults to $world.state.json, if not set",
    )
    parser.add_argument(
        "--steps", type=int, default=10, help="The number of simulation steps to run"
    )
    parser.add_argument(
        "--systems",
        type=str,
        nargs="*",
        help="Extra logic systems to run in the simulation",
    )
    parser.add_argument(
        "--theme", type=str, default="fantasy", help="The theme of the generated world"
    )
    parser.add_argument(
        "--world",
        type=str,
        default="world",
        help="The file to save the generated world to",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    world_file = args.world + ".json"
    world_state_file = args.state or (args.world + ".state.json")

    players = []
    if args.player:
        players.append(args.player)

    memory = {}
    if path.exists(world_state_file):
        logger.info(f"Loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load(f))

        set_step(state.step)

        memory = state.memory
        world = state.world
        world.name = args.world
    elif path.exists(world_file):
        logger.info(f"Loading world from {world_file}")
        with open(world_file, "r") as f:
            world = World(**load(f))
    else:
        logger.info(f"Generating a new {args.theme} world")
        llm = agent_easy_connect()
        agent = Agent(
            "World Builder",
            f"You are an experienced game master creating a visually detailed {args.theme} world for a new adventure. {args.flavor}",
            {},
            llm,
        )
        world = generate_world(
            agent,
            args.world,
            args.theme,
            room_count=args.rooms,
            max_rooms=args.max_rooms,
        )
        save_world(world, world_file)

    create_agents(world, memory=memory, players=players)

    # load extra actions
    extra_actions = []
    for action_name in args.actions:
        logger.info(f"Loading extra actions from {action_name}")
        module_actions = load_plugin(action_name)
        logger.info(
            f"Loaded extra actions: {[action.__name__ for action in module_actions]}"
        )
        extra_actions.extend(module_actions)

    # load extra systems
    def snapshot_system(world: World, step: int) -> None:
        logger.debug("Snapshotting world state")
        save_world_state(world, step, world_state_file)

    extra_systems = [(snapshot_system, None)]
    for system_name in args.systems:
        logger.info(f"Loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(
            f"Loaded extra systems: {[system.__name__ for system in module_systems]}"
        )
        extra_systems.append(module_systems)

    # make sure the server system is last
    input_callbacks = []
    result_callbacks = []

    if args.server:
        from adventure.server import (
            launch_server,
            server_input,
            server_result,
            server_system,
        )

        launch_server()
        extra_systems.append((server_system, None))
        input_callbacks.append(server_input)
        result_callbacks.append(server_result)

    # start the sim
    logger.debug("Simulating world: %s", world)
    simulate_world(
        world,
        steps=args.steps,
        actions=extra_actions,
        systems=extra_systems,
        input_callbacks=input_callbacks,
        result_callbacks=result_callbacks,
    )


def load_plugin(name):
    module_name, function_name = name.rsplit(":", 1)
    plugin_module = import_module(module_name)
    plugin_entry = getattr(plugin_module, function_name)
    return plugin_entry()


if __name__ == "__main__":
    main()
