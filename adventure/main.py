from json import load
from logging.config import dictConfig
from os import environ, path
from typing import Callable, Sequence, Tuple

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.loops import loop_retry
from packit.results import multi_function_or_str_result
from packit.toolbox import Toolbox
from packit.utils import logger_with_colors

from adventure.context import set_current_broadcast, set_dungeon_master
from adventure.models import Attributes
from adventure.plugins import load_plugin

# Configure logging
LOG_PATH = "logging.json"
# LOG_PATH = "dev-logging.json"
try:
    if path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            config_logging = load(f)
            dictConfig(config_logging)
    else:
        print("logging config not found")

except Exception as err:
    print("error loading logging config: %s" % (err))

if True:
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
        get_current_step,
        get_current_world,
        set_current_actor,
        set_current_room,
        set_current_step,
        set_current_world,
    )
    from adventure.generate import generate_world
    from adventure.models import Actor, Room, World, WorldState
    from adventure.state import create_agents, save_world, save_world_state

logger = logger_with_colors(__name__, level="DEBUG")

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
        Tuple[Callable[[World, int], None], Callable[[Attributes], str] | None]
    ] = [],
    event_callbacks: Sequence[Callable[[str], None]] = [],
    input_callbacks: Sequence[Callable[[Room, Actor, str], None]] = [],
    result_callbacks: Sequence[Callable[[Room, Actor, str], None]] = [],
):
    logger.info("Simulating the world")
    set_current_world(world)

    # set up a broadcast callback
    def broadcast_callback(message):
        logger.info(message)
        for callback in event_callbacks:
            callback(message)

    set_current_broadcast(broadcast_callback)

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
        current_step = get_current_step()
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
                    logger.info(
                        f"calling input callback for {actor_name}: {callback.__name__}"
                    )
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
                    "You can only perform one action per turn. What is your next action?"
                    # Pick the most important action and save the rest for later."
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

        set_current_step(current_step + 1)


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
        "--discord", type=bool, help="Whether to run the simulation in a Discord bot"
    )
    parser.add_argument(
        "--flavor",
        type=str,
        default="",
        help="Some additional flavor text for the generated world",
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
        "--optional-actions", type=bool, help="Whether to include optional actions"
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
        help="Extra systems to run in the simulation",
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

    # set up callbacks
    event_callbacks = []
    input_callbacks = []
    result_callbacks = []

    if args.discord:
        from adventure.discord_bot import bot_action, bot_event, bot_result, launch_bot

        launch_bot()
        event_callbacks.append(bot_event)
        input_callbacks.append(bot_action)
        result_callbacks.append(bot_result)

    if args.server:
        from adventure.server import (
            launch_server,
            server_action,
            server_event,
            server_result,
            server_system,
        )

        launch_server()
        event_callbacks.append(server_event)
        input_callbacks.append(server_action)
        result_callbacks.append(server_result)

    memory = {}
    if path.exists(world_state_file):
        logger.info(f"Loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load(f))

        set_current_step(state.step)

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
        world_builder = Agent(
            "World Builder",
            f"You are an experienced game master creating a visually detailed {args.theme} world for a new adventure. {args.flavor}",
            {},
            llm,
        )

        world = None

        def broadcast_callback(message):
            logger.info(message)
            for callback in event_callbacks:
                callback(message)
            if args.server and world:
                server_system(world, 0)

        world = generate_world(
            world_builder,
            args.world,
            args.theme,
            room_count=args.rooms,
            max_rooms=args.max_rooms,
            callback=broadcast_callback,
        )
        save_world(world, world_file)

    create_agents(world, memory=memory, players=players)
    if args.server:
        server_system(world, 0)

    # load extra actions
    extra_actions = []
    for action_name in args.actions or []:
        logger.info(f"Loading extra actions from {action_name}")
        module_actions = load_plugin(action_name)
        logger.info(
            f"Loaded extra actions: {[action.__name__ for action in module_actions]}"
        )
        extra_actions.extend(module_actions)

    if args.optional_actions:
        logger.info("Loading optional actions")
        from adventure.optional_actions import init as init_optional_actions

        optional_actions = init_optional_actions()
        logger.info(
            f"Loaded optional actions: {[action.__name__ for action in optional_actions]}"
        )
        extra_actions.extend(optional_actions)

    # load extra systems
    def snapshot_system(world: World, step: int) -> None:
        logger.debug("Snapshotting world state")
        save_world_state(world, step, world_state_file)

    extra_systems = [(snapshot_system, None)]
    for system_name in args.systems or []:
        logger.info(f"Loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(
            f"Loaded extra systems: {[component.__name__ for system in module_systems for component in system]}"
        )
        extra_systems.extend(module_systems)

    # make sure the server system runs after any updates
    if args.server:
        extra_systems.append((server_system, None))

    # create the DM
    llm = agent_easy_connect()
    world_builder = Agent(
        "dungeon master",
        (
            f"You are the dungeon master in charge of a {world.theme} world. Be creative and original, and come up with "
            f"interesting events that will keep players interested. {args.flavor}"
            "Do not to repeat yourself unless you are given the same prompt with the same characters and actions."
        ),
        {},
        llm,
    )
    set_dungeon_master(world_builder)

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


if __name__ == "__main__":
    main()
