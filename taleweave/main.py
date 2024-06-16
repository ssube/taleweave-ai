import argparse
import atexit
from glob import glob
from logging.config import dictConfig
from os import environ, path
from typing import List

from dotenv import load_dotenv
from packit.utils import logger_with_colors

# this is the ONLY taleweave import allowed before the logger has been created
from taleweave.utils.file import load_yaml

# load environment variables before anything else
load_dotenv(environ.get("TALEWEAVE_ENV", ".env"), override=True)

# configure logging
# TODO: move this to a separate module

LOG_PATH = environ.get("TALEWEAVE_LOGGING", "logging.json")
try:
    if path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            config_logging = load_yaml(f)
            dictConfig(config_logging)
    else:
        print(f"logging config not found at {LOG_PATH}")

except Exception as err:
    print(f"error loading logging config: {err}")


# start the debugger, if needed
if environ.get("DEBUG", "false").lower() in ["true", "1", "yes", "t", "y"]:
    logger = logger_with_colors(__name__, level="DEBUG")

    import debugpy

    debugpy.listen(5679)
    logger.warning("waiting for debugger to attach...")
    debugpy.wait_for_client()
else:
    logger = logger_with_colors(__name__)


if True:
    from taleweave.context import (
        get_prompt_library,
        set_current_world,
        set_game_config,
        set_game_systems,
        subscribe,
    )
    from taleweave.engine import load_or_generate_world, simulate_world
    from taleweave.game_system import GameSystem
    from taleweave.models.config import DEFAULT_CONFIG, Config
    from taleweave.models.entity import World
    from taleweave.models.event import GenerateEvent
    from taleweave.models.files import TemplateFile, WorldPrompt
    from taleweave.models.prompt import PromptLibrary
    from taleweave.plugins import load_plugin
    from taleweave.state import save_world_state
    from taleweave.systems.action import init_action
    from taleweave.systems.planning import init_planning


def int_or_inf(value: str) -> float | int:
    if value == "inf":
        return float("inf")

    return int(value)


# main
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and simulate a text adventure world"
    )

    # config arguments
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
        "--server",
        action="store_true",
        help="Whether to run the websocket server",
    )

    # data and plugin arguments
    parser.add_argument(
        "--actions",
        type=str,
        nargs="*",
        help="Extra actions to include in the simulation",
    )
    parser.add_argument(
        "--prompts",
        type=str,
        nargs="*",
        help="The file to load game prompts from",
    )
    parser.add_argument(
        "--systems",
        type=str,
        nargs="*",
        help="Extra systems to run in the simulation",
    )

    # generation arguments
    parser.add_argument(
        "--add-rooms",
        default=0,
        type=int,
        help="The number of new rooms to generate before starting the simulation",
    )
    parser.add_argument(
        "--rooms",
        type=int,
        help="The number of rooms to generate",
    )

    # simulation arguments
    parser.add_argument(
        "--turns",
        type=int_or_inf,
        default=10,
        help="The number of simulation turns to run",
    )

    # world arguments
    parser.add_argument(
        "--world",
        type=str,
        default="world",
        help="The file to save the generated world to",
    )
    parser.add_argument(
        "--world-flavor",
        type=str,
        default="",
        help="Some additional flavor text for the generated world",
    )
    parser.add_argument(
        "--world-state",
        type=str,
        help="The file to save the world state to. Defaults to $world.state.json, if not set",
    )
    parser.add_argument(
        "--world-template",
        type=str,
        help="The template file to load the world prompt from",
    )
    parser.add_argument(
        "--world-theme",
        type=str,
        default="fantasy",
        help="The theme of the generated world",
    )
    return parser.parse_args()


def get_world_prompt(args) -> WorldPrompt:
    if args.world_template:
        prompt_file, prompt_name = args.world_template.split(":")
        with open(prompt_file, "r") as f:
            prompts = TemplateFile(**load_yaml(f))
            for prompt in prompts.templates:
                if prompt.name == prompt_name:
                    return prompt

        logger.warning(f"prompt {prompt_name} not found in {prompt_file}")

    return WorldPrompt(
        name=args.world,
        theme=args.world_theme,
        flavor=args.world_flavor,
    )


def load_prompt_library(args) -> None:
    if args.prompts:
        prompt_files = []
        for prompt_file in args.prompts:
            prompt_files.extend(glob(prompt_file, recursive=True))

        for prompt_file in prompt_files:
            with open(prompt_file, "r") as f:
                new_library = PromptLibrary(**load_yaml(f))
                logger.info(f"loaded prompt library from {prompt_file}")
                library = get_prompt_library()
                library.prompts.update(new_library.prompts)

    return None


def main():
    args = parse_args()

    if args.config:
        with open(args.config, "r") as f:
            config = Config(**load_yaml(f))
            set_game_config(config)
    else:
        config = DEFAULT_CONFIG

    load_prompt_library(args)

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

    # load extra actions from plugins
    for action_name in args.actions or []:
        logger.info(f"loading extra actions from {action_name}")
        action_group, module_actions = load_plugin(action_name)
        logger.info(
            f"loaded extra actions to group '{action_group}': {[action.__name__ for action in module_actions]}"
        )

    # set up the game systems
    systems: List[GameSystem] = []
    systems.extend(init_planning())
    systems.extend(init_action())

    # load extra systems from plugins
    for system_name in args.systems or []:
        logger.info(f"loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(f"loaded extra systems: {module_systems}")
        systems.extend(module_systems)

    # make sure the server system runs after any updates
    if args.server:
        from taleweave.server.websocket import server_system

        systems.append(GameSystem(name="server", simulate=server_system))

    set_game_systems(systems)

    # load or generate the world
    world_prompt = get_world_prompt(args)
    world, world_state_file, world_turn = load_or_generate_world(
        args.world,
        args.world_state,
        config,
        players,
        systems,
        world_prompt=world_prompt,
        room_count=args.rooms,
        add_rooms=args.add_rooms,
    )
    set_current_world(world)

    # make sure the snapshot system runs last
    def snapshot_system(world: World, turn: int, data: None = None) -> None:
        logger.info("taking snapshot of world state")
        save_world_state(world, turn, world_state_file)

    systems.append(GameSystem(name="snapshot", simulate=snapshot_system))

    # hack: send a snapshot to the websocket server
    if args.server:
        server_system(world, world_turn)

    simulate_world(world, systems, args.turns)


if __name__ == "__main__":
    main()
