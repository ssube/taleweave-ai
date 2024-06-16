import argparse
from os import environ, path
from typing import List, Tuple

from dotenv import load_dotenv
from packit.utils import logger_with_colors

from taleweave.context import get_dungeon_master, get_game_systems, set_game_systems
from taleweave.engine import load_or_initialize_system_data
from taleweave.game_system import GameSystem
from taleweave.generate import (
    generate_character,
    generate_item,
    generate_portals,
    generate_room,
    link_rooms,
)
from taleweave.main import load_prompt_library
from taleweave.models.base import dump_model
from taleweave.models.entity import World, WorldState
from taleweave.plugins import load_plugin
from taleweave.utils.file import load_yaml, save_yaml
from taleweave.utils.search import (
    find_character,
    find_item,
    find_portal,
    find_room,
    list_characters,
    list_items,
    list_portals,
    list_rooms,
)
from taleweave.utils.world import describe_entity

ENTITY_TYPES = ["room", "portal", "item", "character"]

logger = logger_with_colors(__name__)


# load environment variables before anything else
load_dotenv(environ.get("TALEWEAVE_ENV", ".env"), override=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Taleweave Editor")
    parser.add_argument("--prompts", type=str, nargs="*", help="Prompt files to load")
    parser.add_argument("--state", type=str, help="State file to edit")
    parser.add_argument("--world", type=str, help="World file to edit")
    parser.add_argument("--systems", type=str, nargs="*", help="Game systems to load")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True

    # Set up the 'list' command
    list_parser = subparsers.add_parser("list", help="List entities of a specific type")
    list_parser.add_argument(
        "type", help="Type of entity to list", choices=ENTITY_TYPES
    )

    # Set up the 'describe' command
    describe_parser = subparsers.add_parser("describe", help="Describe an entity")
    describe_parser.add_argument(
        "type", help="Type of entity to describe", choices=ENTITY_TYPES
    )
    describe_parser.add_argument("entity", type=str, help="Entity to describe")

    # Set up the 'create' command
    create_parser = subparsers.add_parser("create", help="Create an entity")
    create_parser.add_argument(
        "type", help="Type of entity to create", choices=ENTITY_TYPES
    )
    create_parser.add_argument("name", type=str, help="Name of the entity to create")
    create_parser.add_argument("--room", type=str, help="Room the entity is in")

    # Set up the 'generate' command
    generate_parser = subparsers.add_parser("generate", help="Generate an entity")
    generate_parser.add_argument(
        "type", help="Type of entity to generate", choices=ENTITY_TYPES
    )
    generate_parser.add_argument(
        "prompt", type=str, help="Prompt to generate the entity"
    )
    generate_parser.add_argument("--room", type=str, help="Room the entity is in")
    generate_parser.add_argument(
        "--dest-room", type=str, help="Destination room for portals"
    )

    # Set up the 'delete' command
    delete_parser = subparsers.add_parser("delete", help="Delete an entity")
    delete_parser.add_argument(
        "type", help="Type of entity to delete", choices=ENTITY_TYPES
    )
    delete_parser.add_argument("entity", type=str, help="Entity to delete")

    # Set up the 'update' command
    update_parser = subparsers.add_parser("update", help="Update an entity")
    update_parser.add_argument(
        "type", help="Type of entity to update", choices=ENTITY_TYPES
    )
    update_parser.add_argument("entity", type=str, help="Entity to update")
    update_parser.add_argument("--backstory", type=str, help="Backstory of the entity")
    update_parser.add_argument(
        "--description", type=str, help="Description of the entity"
    )

    # Set up the 'link' command
    link_parser = subparsers.add_parser("link", help="Link rooms")
    link_parser.add_argument(
        "rooms",
        type=str,
        nargs="*",
        help="Rooms to link. Leave blank to link all rooms.",
    )

    return parser.parse_args()


def load_world(state_file, world_file) -> Tuple[World, WorldState | None]:
    systems = get_game_systems()

    if state_file and path.exists(state_file):
        with open(state_file, "r") as f:
            state = WorldState(**load_yaml(f))

        load_or_initialize_system_data(world_file, systems, state.world)

        return (state.world, state)

    if world_file and path.exists(world_file):
        with open(world_file, "r") as f:
            world = World(**load_yaml(f))

        load_or_initialize_system_data(world_file, systems, world)

        return (world, None)

    raise ValueError("No state or world file found")


def save_world(state_file, world_file, world: World, state: WorldState | None):
    """
    Save the world to the given files.

    This is intentionally a noop stub until the editor is more stable.
    """
    if state:
        logger.warning(f"Saving world {world.name} to {state_file}")
        return

        with open(state_file, "w") as f:
            save_yaml(f, dump_model(WorldState, state))
    else:
        logger.warning(f"Saving world {world.name} to {world_file}")
        return

        with open(world_file, "w") as f:
            save_yaml(f, dump_model(World, world))


def command_list(args):
    world, _ = load_world(args.state, args.world)
    logger.info(f"Listing {args.type}s from world {world.name}")

    if args.type == "room":
        for room in list_rooms(world):
            logger.info(room.name)

    if args.type == "portal":
        for portal in list_portals(world):
            logger.info(portal.name)

    if args.type == "item":
        for item in list_items(
            world, include_character_inventory=True, include_item_inventory=True
        ):
            logger.info(item.name)

    if args.type == "character":
        for character in list_characters(world):
            logger.info(character.name)


def command_describe(args):
    world, _ = load_world(args.state, args.world)
    logger.info(f"Describing {args.entity} from world {world.name}")

    if args.type == "room":
        room = find_room(world, args.entity)
        if not room:
            logger.error(f"Room {args.entity} not found")
        else:
            logger.info(describe_entity(room))

    if args.type == "portal":
        portal = find_portal(world, args.entity)
        if not portal:
            logger.error(f"Portal {args.entity} not found")
        else:
            logger.info(describe_entity(portal))

    if args.type == "item":
        item = find_item(
            world,
            args.entity,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if not item:
            logger.error(f"Item {args.entity} not found")
        else:
            logger.info(describe_entity(item))

    if args.type == "character":
        character = find_character(world, args.entity)
        if not character:
            logger.error(f"Character {args.entity} not found")
        else:
            logger.info(describe_entity(character))


def command_create(args):
    world, state = load_world(args.state, args.world)
    logger.info(f"Create {args.type} named {args.name} in world {world.name}")

    # TODO: Create the entity

    save_world(args.state, args.world, world, state)


def command_generate(args):
    world, state = load_world(args.state, args.world)
    logger.info(
        f"Generating {args.type} for world {world.name} using prompt: {args.prompt}"
    )

    dungeon_master = get_dungeon_master()
    systems = get_game_systems()

    if args.type == "room":
        room = generate_room(dungeon_master, world, systems)
        world.rooms.append(room)

    if args.type == "portal":
        source_room = find_room(world, args.room)
        if not source_room:
            logger.error(f"Room {args.room} not found")
            return

        destination_room = find_room(world, args.dest_room)
        if not destination_room:
            logger.error(f"Room {args.dest_room} not found")
            return

        outgoing_portal, incoming_portal = generate_portals(
            dungeon_master, world, source_room, destination_room, systems
        )
        source_room.portals.append(outgoing_portal)
        destination_room.portals.append(incoming_portal)

    if args.type == "item":
        # TODO: add item to character or container inventory
        room = find_room(world, args.room)
        if not room:
            logger.error(f"Room {args.room} not found")
            return

        item = generate_item(dungeon_master, world, systems)
        room.items.append(item)

    if args.type == "character":
        room = find_room(world, args.room)
        if not room:
            logger.error(f"Room {args.room} not found")
            return

        character = generate_character(
            dungeon_master, world, systems, room, args.prompt
        )
        room.characters.append(character)

    save_world(args.state, args.world, world, state)


def command_delete(args):
    world, state = load_world(args.state, args.world)
    logger.info(f"Delete {args.entity} from world {world.name}")

    # TODO: Delete the entity

    save_world(args.state, args.world, world, state)


def command_update(args):
    world, state = load_world(args.state, args.world)
    logger.info(f"Update {args.entity} in world {world.name}")

    if args.type == "room":
        room = find_room(world, args.entity)
        if not room:
            logger.error(f"Room {args.entity} not found")
        else:
            logger.info(describe_entity(room))

    if args.type == "portal":
        portal = find_portal(world, args.entity)
        if not portal:
            logger.error(f"Portal {args.entity} not found")
        else:
            logger.info(describe_entity(portal))

    if args.type == "item":
        item = find_item(
            world,
            args.entity,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if not item:
            logger.error(f"Item {args.entity} not found")
        else:
            logger.info(describe_entity(item))

    if args.type == "character":
        character = find_character(world, args.entity)
        if not character:
            logger.error(f"Character {args.entity} not found")
        else:
            if args.backstory:
                character.backstory = args.backstory

            if args.description:
                character.description = args.description

            logger.info(describe_entity(character))

    save_world(args.state, args.world, world, state)


def command_link(args):
    world, state = load_world(args.state, args.world)
    logger.info(f"Linking rooms {args.rooms} in world {world.name}")

    dungeon_master = get_dungeon_master()
    systems = get_game_systems()

    link_rooms(dungeon_master, world, systems)

    save_world(args.state, args.world, world, state)


COMMAND_TABLE = {
    "list": command_list,
    "describe": command_describe,
    "create": command_create,
    "generate": command_generate,
    "delete": command_delete,
    "update": command_update,
    "link": command_link,
}


def main():
    args = parse_args()
    logger.debug(f"running with args: {args}")

    load_prompt_library(args)

    # load game systems before executing commands
    systems: List[GameSystem] = []
    for system_name in args.systems or []:
        logger.info(f"loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        logger.info(f"loaded extra systems: {module_systems}")
        systems.extend(module_systems)

    set_game_systems(systems)

    command = COMMAND_TABLE[args.command]
    command(args)


if __name__ == "__main__":
    main()
