import atexit
from functools import partial
from logging.config import dictConfig
from os import environ, path
from typing import List

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.memory import make_limited_memory
from packit.utils import logger_with_colors

from taleweave.utils.file import load_yaml

# configure logging
LOG_PATH = "logging.json"
try:
    if path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            config_logging = load_yaml(f)
            dictConfig(config_logging)
    else:
        print("logging config not found")

except Exception as err:
    print("error loading logging config: %s" % (err))


logger = logger_with_colors(__name__)  # , level="DEBUG")

load_dotenv(environ.get("ADVENTURE_ENV", ".env"), override=True)

if True:
    from taleweave.context import (
        get_system_data,
        set_current_turn,
        set_dungeon_master,
        set_system_data,
        subscribe,
    )
    from taleweave.game_system import GameSystem
    from taleweave.generate import generate_room, generate_world, link_rooms
    from taleweave.models.config import DEFAULT_CONFIG, Config
    from taleweave.models.entity import World, WorldState
    from taleweave.models.event import GenerateEvent
    from taleweave.models.files import PromptFile, WorldPrompt
    from taleweave.plugins import load_plugin
    from taleweave.simulate import simulate_world
    from taleweave.state import (
        MEMORY_LIMIT,
        create_agents,
        save_world,
        save_world_state,
    )

# start the debugger, if needed
if environ.get("DEBUG", "false").lower() == "true":
    import debugpy

    debugpy.listen(5679)
    logger.info("waiting for debugger to attach...")
    debugpy.wait_for_client()


memory_factory = partial(make_limited_memory, limit=MEMORY_LIMIT)


def int_or_inf(value: str) -> float | int:
    if value == "inf":
        return float("inf")

    return int(value)


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
        "--add-rooms",
        default=0,
        type=int,
        help="The number of new rooms to generate before starting the simulation",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="The file to load additional configuration from",
    )
    parser.add_argument(
        "--discord",
        action="store_true",
        help="Whether to run the simulation in a Discord bot",
    )
    parser.add_argument(
        "--flavor",
        type=str,
        default="",
        help="Some additional flavor text for the generated world",
    )
    parser.add_argument(
        "--optional-actions",
        action="store_true",
        help="Whether to include optional actions in the simulation",
    )
    parser.add_argument(
        "--player",
        type=str,
        help="The name of the character to play as",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Whether to run the render thread",
    )
    parser.add_argument(
        "--render-generated",
        action="store_true",
        help="Whether to render entities as they are generated",
    )
    parser.add_argument(
        "--rooms",
        type=int,
        help="The number of rooms to generate",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Whether to run the websocket server",
    )
    parser.add_argument(
        "--state",
        type=str,
        help="The file to save the world state to. Defaults to $world.state.json, if not set",
    )
    parser.add_argument(
        "--turns",
        type=int_or_inf,
        default=10,
        help="The number of simulation turns to run",
    )
    parser.add_argument(
        "--systems",
        type=str,
        nargs="*",
        help="Extra systems to run in the simulation",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="fantasy",
        help="The theme of the generated world",
    )
    parser.add_argument(
        "--world",
        type=str,
        default="world",
        help="The file to save the generated world to",
    )
    parser.add_argument(
        "--world-template",
        type=str,
        help="The template file to load the world prompt from",
    )
    return parser.parse_args()


def get_world_prompt(args) -> WorldPrompt:
    if args.world_template:
        prompt_file, prompt_name = args.world_template.split(":")
        with open(prompt_file, "r") as f:
            prompts = PromptFile(**load_yaml(f))
            for prompt in prompts.prompts:
                if prompt.name == prompt_name:
                    return prompt

        logger.warning(f"prompt {prompt_name} not found in {prompt_file}")

    return WorldPrompt(
        name=args.world,
        theme=args.theme,
        flavor=args.flavor,
    )


def load_or_initialize_system_data(args, systems: List[GameSystem], world: World):
    for system in systems:
        if system.data:
            system_data_file = f"{args.world}.{system.name}.json"

            if path.exists(system_data_file):
                logger.info(f"loading system data from {system_data_file}")
                data = system.data.load(system_data_file)
                set_system_data(system.name, data)
            else:
                logger.info(f"no system data found at {system_data_file}")
                if system.initialize:
                    data = system.initialize(world)
                    set_system_data(system.name, data)


def save_system_data(args, systems: List[GameSystem]):
    for system in systems:
        if system.data:
            system_data_file = f"{args.world}.{system.name}.json"
            logger.info(f"saving system data to {system_data_file}")
            system.data.save(system_data_file, get_system_data(system.name))


def load_or_generate_world(
    args, players, systems: List[GameSystem], world_prompt: WorldPrompt
):
    world_file = args.world + ".json"
    world_state_file = args.state or (args.world + ".state.json")
    add_rooms = args.add_rooms

    memory = {}
    turn = 0

    # prepare an agent for the world builder
    llm = agent_easy_connect()
    world_builder = Agent(
        "World Builder",
        f"You are an experienced game master creating a visually detailed world for a new adventure. "
        f"{world_prompt.flavor}. The theme is: {world_prompt.theme}.",
        {},
        llm,
        memory_factory=memory_factory,
    )

    if path.exists(world_state_file):
        logger.info(f"loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load_yaml(f))

        set_current_turn(state.turn)
        load_or_initialize_system_data(args, systems, state.world)

        memory = state.memory
        turn = state.turn
        world = state.world
    elif path.exists(world_file):
        logger.info(f"loading world from {world_file}")
        with open(world_file, "r") as f:
            world = World(**load_yaml(f))

        load_or_initialize_system_data(args, systems, world)
    else:
        logger.info(f"generating a new world using theme: {world_prompt.theme}")
        world = generate_world(
            world_builder,
            args.world,
            world_prompt.theme,
            systems,
            room_count=args.rooms,
        )
        save_world(world, world_file)
        save_system_data(args, systems)

    new_rooms = []
    for i in range(add_rooms):
        logger.info(f"generating room {i + 1} of {add_rooms}")
        room = generate_room(world_builder, world, systems)
        new_rooms.append(room)
        world.rooms.append(room)

    if new_rooms:
        link_rooms(world_builder, world, systems, new_rooms)

    create_agents(world, memory=memory, players=players)
    return (world, world_state_file, turn)


def main():
    args = parse_args()

    if args.config:
        with open(args.config, "r") as f:
            config = Config(**load_yaml(f))
    else:
        config = DEFAULT_CONFIG

    players = []
    if args.player:
        players.append(args.player)

    # launch other threads
    threads = []

    if args.render:
        from taleweave.render.comfy import launch_render, render_generated

        threads.extend(launch_render(config.render))
        if args.render_generated:
            subscribe(GenerateEvent, render_generated)

    if args.discord:
        from taleweave.bot.discord import launch_bot

        threads.extend(launch_bot(config.bot.discord))

    if args.server:
        from taleweave.server.websocket import launch_server

        threads.extend(launch_server(config.server.websocket))

    # register the thread shutdown handler
    def shutdown_threads():
        for thread in threads:
            thread.join(1.0)

    atexit.register(shutdown_threads)

    # load built-in but optional actions
    extra_actions = []
    if args.optional_actions:
        logger.info("loading optional actions")
        from taleweave.actions.optional import init as init_optional_actions

        optional_actions = init_optional_actions()
        logger.info(
            f"loaded optional actions: {[action.__name__ for action in optional_actions]}"
        )
        extra_actions.extend(optional_actions)

    # load extra actions from plugins
    for action_name in args.actions or []:
        logger.info(f"loading extra actions from {action_name}")
        module_actions = load_plugin(action_name)
        logger.info(
            f"loaded extra actions: {[action.__name__ for action in module_actions]}"
        )
        extra_actions.extend(module_actions)

    # load extra systems from plugins
    extra_systems: List[GameSystem] = []
    for system_name in args.systems or []:
        logger.info(f"loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(f"loaded extra systems: {module_systems}")
        extra_systems.extend(module_systems)

    # make sure the server system runs after any updates
    if args.server:
        from taleweave.server.websocket import server_system

        extra_systems.append(GameSystem(name="server", simulate=server_system))

    # load or generate the world
    world_prompt = get_world_prompt(args)
    world, world_state_file, world_turn = load_or_generate_world(
        args, players, extra_systems, world_prompt=world_prompt
    )

    # make sure the snapshot system runs last
    def snapshot_system(world: World, turn: int, data: None = None) -> None:
        logger.info("taking snapshot of world state")
        save_world_state(world, turn, world_state_file)

    extra_systems.append(GameSystem(name="snapshot", simulate=snapshot_system))

    # hack: send a snapshot to the websocket server
    if args.server:
        server_system(world, world_turn)

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
        memory_factory=memory_factory,
    )
    set_dungeon_master(world_builder)

    # start the sim
    logger.debug("simulating world: %s", world)
    simulate_world(
        world,
        turns=args.turns,
        actions=extra_actions,
        systems=extra_systems,
    )


if __name__ == "__main__":
    main()
