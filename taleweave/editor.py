import argparse
from os import path
from typing import List, Tuple

from taleweave.context import get_dungeon_master, get_game_systems, set_game_systems
from taleweave.game_system import GameSystem
from taleweave.generate import (
    generate_character,
    generate_item,
    generate_portals,
    generate_room,
)
from taleweave.main import load_or_initialize_system_data
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


def parse_args():
    parser = argparse.ArgumentParser(description="Taleweave Editor")
    parser.add_argument("--state", type=str, help="State file to edit")
    parser.add_argument("--world", type=str, help="World file to edit")
    parser.add_argument("--systems", type=str, nargs="*", help="Game systems to load")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True

    # Set up the 'list' command
    list_parser = subparsers.add_parser(
        "list", help="List all entities or entities of a specific type"
    )
    list_parser.add_argument(
        "type", help="Type of entity to list", choices=ENTITY_TYPES, nargs="?"
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

    return parser.parse_args()


def load_world(state_file, world_file) -> Tuple[World, WorldState | None]:
    systems = []

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
    if state:
        print(f"Saving world {world.name} to {state_file}")
        return

        with open(state_file, "w") as f:
            save_yaml(f, dump_model(WorldState, state))
    else:
        print(f"Saving world {world.name} to {world_file}")
        return

        with open(world_file, "w") as f:
            save_yaml(f, dump_model(World, world))


def command_list(args):
    print(f"Listing {args.type}s")
    world, _ = load_world(args.state, args.world)
    print(world.name)

    if args.type == "room":
        for room in list_rooms(world):
            print(room.name)

    if args.type == "portal":
        for portal in list_portals(world):
            print(portal.name)

    if args.type == "item":
        for item in list_items(
            world, include_character_inventory=True, include_item_inventory=True
        ):
            print(item.name)

    if args.type == "character":
        for character in list_characters(world):
            print(character.name)


def command_describe(args):
    print(f"Describing {args.entity}")
    world, _ = load_world(args.state, args.world)
    print(world.name)

    if args.type == "room":
        room = find_room(world, args.entity)
        if not room:
            print(f"Room {args.entity} not found")
        else:
            print(describe_entity(room))

    if args.type == "portal":
        portal = find_portal(world, args.entity)
        if not portal:
            print(f"Portal {args.entity} not found")
        else:
            print(describe_entity(portal))

    if args.type == "item":
        item = find_item(
            world,
            args.entity,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if not item:
            print(f"Item {args.entity} not found")
        else:
            print(describe_entity(item))

    if args.type == "character":
        character = find_character(world, args.entity)
        if not character:
            print(f"Character {args.entity} not found")
        else:
            print(describe_entity(character))


def command_create(args):
    print(f"Create {args.type} named {args.name}")
    world, state = load_world(args.state, args.world)
    print(world.name)

    # TODO: Create the entity

    save_world(args.state, args.world, world, state)


def command_generate(args):
    print(f"Generate {args.type} with prompt: {args.prompt}")
    world, state = load_world(args.state, args.world)
    print(world.name)

    dungeon_master = get_dungeon_master()
    systems = get_game_systems()

    # TODO: Generate the entity
    if args.type == "room":
        room = generate_room(dungeon_master, world, systems)
        world.rooms.append(room)

    if args.type == "portal":
        portal = generate_portals(dungeon_master, world, "TODO", "TODO", systems)
        # TODO: Add portal to room and generate reverse portal from destination room

    if args.type == "item":
        item = generate_item(dungeon_master, world, systems)
        # TODO: Add item to room or character inventory

    if args.type == "character":
        character = generate_character(
            dungeon_master, world, systems, "TODO", args.prompt
        )
        # TODO: Add character to room

    save_world(args.state, args.world, world, state)


def command_delete(args):
    print(f"Delete {args.entity}")
    world, state = load_world(args.state, args.world)
    print(world.name)

    # TODO: Delete the entity

    save_world(args.state, args.world, world, state)


def command_update(args):
    print(f"Update {args.entity}")
    world, state = load_world(args.state, args.world)
    print(world.name)

    if args.type == "room":
        room = find_room(world, args.entity)
        if not room:
            print(f"Room {args.entity} not found")
        else:
            print(describe_entity(room))

    if args.type == "portal":
        portal = find_portal(world, args.entity)
        if not portal:
            print(f"Portal {args.entity} not found")
        else:
            print(describe_entity(portal))

    if args.type == "item":
        item = find_item(
            world,
            args.entity,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if not item:
            print(f"Item {args.entity} not found")
        else:
            print(describe_entity(item))

    if args.type == "character":
        character = find_character(world, args.entity)
        if not character:
            print(f"Character {args.entity} not found")
        else:
            if args.backstory:
                character.backstory = args.backstory

            if args.description:
                character.description = args.description

            print(describe_entity(character))

    save_world(args.state, args.world, world, state)


COMMAND_TABLE = {
    "list": command_list,
    "describe": command_describe,
    "create": command_create,
    "generate": command_generate,
    "delete": command_delete,
    "update": command_update,
}


def main():
    args = parse_args()
    print(args)

    # load game systems before executing commands
    systems: List[GameSystem] = []
    for system_name in args.systems or []:
        print(f"loading extra systems from {system_name}")
        module_systems = load_plugin(system_name)
        print(f"loaded extra systems: {module_systems}")
        systems.extend(module_systems)

    set_game_systems(systems)

    command = COMMAND_TABLE[args.command]
    command(args)


if __name__ == "__main__":
    main()
