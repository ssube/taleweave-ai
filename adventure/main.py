import atexit
from logging.config import dictConfig
from os import environ, path
from typing import List

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.utils import logger_with_colors
from yaml import Loader, load

from adventure.context import set_current_step, set_dungeon_master
from adventure.generate import generate_world
from adventure.models.entity import World, WorldState
from adventure.models.event import EventCallback, GameEvent
from adventure.models.files import PromptFile, WorldPrompt
from adventure.plugins import load_plugin
from adventure.simulate import simulate_world
from adventure.state import create_agents, save_world, save_world_state


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


logger = logger_with_colors(__name__, level="DEBUG")

load_dotenv(environ.get("ADVENTURE_ENV", ".env"), override=True)


# start the debugger, if needed
if environ.get("DEBUG", "false").lower() == "true":
    import debugpy

    debugpy.listen(5679)
    logger.info("waiting for debugger to attach...")
    debugpy.wait_for_client()


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
    parser.add_argument(
        "--world-prompt",
        type=str,
        help="The file to load the world prompt from",
    )
    return parser.parse_args()


def get_world_prompt(args) -> WorldPrompt:
    if args.world_prompt:
        prompt_file, prompt_name = args.world_prompt.split(":")
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


def load_or_generate_world(args, players, callbacks, world_prompt: WorldPrompt):
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

        world = None

        def broadcast_callback(event: GameEvent):
            logger.info(event)
            for callback in callbacks:
                callback(event)

        world = generate_world(
            world_builder,
            args.world,
            world_prompt.theme,
            room_count=args.rooms,
            max_rooms=args.max_rooms,
            callback=broadcast_callback,
        )
        save_world(world, world_file)

    create_agents(world, memory=memory, players=players)
    return (world, world_state_file)


def main():
    args = parse_args()

    players = []
    if args.player:
        players.append(args.player)

    # set up callbacks
    callbacks: List[EventCallback] = []

    # launch other threads
    threads = []
    if args.discord:
        from adventure.discord_bot import bot_event, launch_bot

        threads.extend(launch_bot())
        callbacks.append(bot_event)

    if args.server:
        from adventure.server import launch_server, server_event, server_system

        threads.extend(launch_server())
        callbacks.append(server_event)

    # register the thread shutdown handler
    def shutdown_threads():
        for thread in threads:
            thread.join(1.0)

    atexit.register(shutdown_threads)

    # load built-in but optional actions
    extra_actions = []
    if args.optional_actions:
        logger.info("loading optional actions")
        from adventure.optional_actions import init as init_optional_actions

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
    extra_systems = []
    for system_name in args.systems or []:
        logger.info(f"loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(
            f"loaded extra systems: {[component.__name__ for system in module_systems for component in system]}"
        )
        extra_systems.extend(module_systems)

    # make sure the server system runs after any updates
    if args.server:
        extra_systems.append((server_system, None))

    # load or generate the world
    world_prompt = get_world_prompt(args)
    world, world_state_file = load_or_generate_world(
        args, players, callbacks, world_prompt=world_prompt
    )

    # make sure the snapshot system runs last
    def snapshot_system(world: World, step: int) -> None:
        logger.info("taking snapshot of world state")
        save_world_state(world, step, world_state_file)

    extra_systems.append((snapshot_system, None))

    # run the systems once to initialize everything
    for system_update, _ in extra_systems:
        system_update(world, 0)

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
        callbacks=callbacks,
    )


if __name__ == "__main__":
    main()
