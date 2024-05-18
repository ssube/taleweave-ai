import atexit
from logging.config import dictConfig
from os import environ, path
from typing import List

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.utils import logger_with_colors
from yaml import Loader, load

from adventure.context import subscribe


def load_yaml(file):
    return load(file, Loader=Loader)


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
    from adventure.context import set_current_step, set_dungeon_master
    from adventure.game_system import GameSystem
    from adventure.generate import generate_world
    from adventure.models.config import DEFAULT_CONFIG, Config
    from adventure.models.entity import World, WorldState
    from adventure.models.event import GenerateEvent
    from adventure.models.files import PromptFile, WorldPrompt
    from adventure.plugins import load_plugin
    from adventure.simulate import simulate_world
    from adventure.state import create_agents, save_world, save_world_state


# start the debugger, if needed
if environ.get("DEBUG", "false").lower() == "true":
    import debugpy

    debugpy.listen(5679)
    logger.info("waiting for debugger to attach...")
    debugpy.wait_for_client()


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
        "--max-rooms",
        default=6,
        type=int,
        help="The maximum number of rooms to generate",
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
        "--steps",
        type=int_or_inf,
        default=10,
        help="The number of simulation steps to run",
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


def load_or_generate_world(args, players, systems, world_prompt: WorldPrompt):
    world_file = args.world + ".json"
    world_state_file = args.state or (args.world + ".state.json")

    memory = {}
    if path.exists(world_state_file):
        logger.info(f"loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load_yaml(f))

        set_current_step(state.step)

        memory = state.memory
        world = state.world
    elif path.exists(world_file):
        logger.info(f"loading world from {world_file}")
        with open(world_file, "r") as f:
            world = World(**load_yaml(f))
    else:
        logger.info(f"generating a new world using theme: {world_prompt.theme}")
        llm = agent_easy_connect()
        world_builder = Agent(
            "World Builder",
            f"You are an experienced game master creating a visually detailed world for a new adventure. "
            f"{world_prompt.flavor}. The theme is: {world_prompt.theme}.",
            {},
            llm,
        )

        world = generate_world(
            world_builder,
            args.world,
            world_prompt.theme,
            room_count=args.rooms,
            max_rooms=args.max_rooms,
        )
        save_world(world, world_file)

        # run the systems once to initialize everything
        for system in systems:
            if system.simulate:
                system.simulate(world, 0)

    create_agents(world, memory=memory, players=players)
    return (world, world_state_file)


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
        from adventure.render.comfy import launch_render, render_generated

        threads.extend(launch_render(config.render))
        if args.render_generated:
            subscribe(GenerateEvent, render_generated)

    if args.discord:
        from adventure.bot.discord import launch_bot

        threads.extend(launch_bot(config.bot.discord))

    if args.server:
        from adventure.server.websocket import launch_server

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
        from adventure.actions.optional import init as init_optional_actions

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
        from adventure.server.websocket import server_system

        extra_systems.append(GameSystem(simulate=server_system))

    # load or generate the world
    world_prompt = get_world_prompt(args)
    world, world_state_file = load_or_generate_world(
        args, players, extra_systems, world_prompt=world_prompt
    )

    # make sure the snapshot system runs last
    def snapshot_system(world: World, step: int) -> None:
        logger.info("taking snapshot of world state")
        save_world_state(world, step, world_state_file)

    extra_systems.append(GameSystem(simulate=snapshot_system))

    # hack: send a snapshot to the websocket server
    if args.server:
        server_system(world, 0)

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
    logger.debug("simulating world: %s", world)
    simulate_world(
        world,
        steps=args.steps,
        actions=extra_actions,
        systems=extra_systems,
    )


if __name__ == "__main__":
    main()
