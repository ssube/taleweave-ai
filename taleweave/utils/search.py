from typing import Any, Generator

from taleweave.models.entity import (
    Character,
    EntityReference,
    Item,
    Portal,
    Room,
    World,
    WorldEntity,
)

from .string import normalize_name


def find_room(world: World, room_name: str) -> Room | None:
    for room in world.rooms:
        if normalize_name(room.name) == normalize_name(room_name):
            return room

    return None


def find_portal(world: World, portal_name: str) -> Portal | None:
    for room in world.rooms:
        portal = find_portal_in_room(room, portal_name)
        if portal:
            return portal

    return None


def find_character(world: World, character_name: str) -> Character | None:
    for room in world.rooms:
        character = find_character_in_room(room, character_name)
        if character:
            return character

    return None


def find_character_in_room(room: Room, character_name: str) -> Character | None:
    for character in room.characters:
        if normalize_name(character.name) == normalize_name(character_name):
            return character

    return None


def find_portal_in_room(room: Room, portal_name: str) -> Portal | None:
    for portal in room.portals:
        if normalize_name(portal.name) == normalize_name(portal_name):
            return portal

    return None


# TODO: allow item or str
def find_item(
    world: World,
    item_name: str,
    include_character_inventory=False,
    include_item_inventory=False,
) -> Item | None:
    for room in world.rooms:
        item = find_item_in_room(
            room, item_name, include_character_inventory, include_item_inventory
        )
        if item:
            return item

    return None


def find_item_in_character(
    character: Character, item_name: str, include_item_inventory=False
) -> Item | None:
    return find_item_in_container(character, item_name, include_item_inventory)


def find_item_in_container(
    container: Character | Item, item_name: str, include_item_inventory=False
) -> Item | None:
    for item in container.items:
        if normalize_name(item.name) == normalize_name(item_name):
            return item

        if include_item_inventory:
            item = find_item_in_container(item, item_name, include_item_inventory)
            if item:
                return item

    return None


def find_item_in_room(
    room: Room,
    item_name: str,
    include_character_inventory=False,
    include_item_inventory=False,
) -> Item | None:
    for item in room.items:
        if normalize_name(item.name) == normalize_name(item_name):
            return item

        if include_item_inventory:
            item = find_item_in_container(item, item_name, include_item_inventory)
            if item:
                return item

    if include_character_inventory:
        for character in room.characters:
            item = find_item_in_character(character, item_name, include_item_inventory)
            if item:
                return item

    return None


def find_containing_room(world: World, entity: Room | Character | Item) -> Room | None:
    if isinstance(entity, Room):
        return entity

    for room in world.rooms:
        if entity in room.characters or entity in room.items:
            return room

    return None


def find_entity_reference(
    world: World, reference: EntityReference
) -> WorldEntity | None:
    """
    Resolve an entity reference to an entity in the world.
    """

    if reference.room:
        return find_room(world, reference.room)

    if reference.character:
        return find_character(world, reference.character)

    if reference.item:
        return find_item(world, reference.item)

    if reference.portal:
        return find_portal(world, reference.portal)

    return None


def list_rooms(world: World) -> Generator[Room, Any, None]:
    for room in world.rooms:
        yield room


def list_portals(world: World) -> Generator[Portal, Any, None]:
    for room in world.rooms:
        for portal in room.portals:
            yield portal


def list_characters(world: World) -> Generator[Character, Any, None]:
    for room in world.rooms:
        for character in room.characters:
            yield character


def list_items(
    world: World, include_character_inventory=True, include_item_inventory=True
) -> Generator[Item, Any, None]:

    for room in world.rooms:
        for item in room.items:
            yield item

            if include_item_inventory:
                yield from list_items_in_container(item)

        if include_character_inventory:
            for character in room.characters:
                for item in character.items:
                    yield item


def list_characters_in_room(room: Room) -> Generator[Character, Any, None]:
    for character in room.characters:
        yield character


def list_items_in_character(
    character: Character, include_item_inventory=True
) -> Generator[Item, Any, None]:
    for item in character.items:
        yield item

        if include_item_inventory:
            yield from list_items_in_container(item)


def list_items_in_container(
    container: Item, include_item_inventory=True
) -> Generator[Item, Any, None]:
    for item in container.items:
        yield item

        if include_item_inventory:
            yield from list_items_in_container(item)


def list_items_in_room(
    room: Room,
    include_character_inventory=True,
    include_item_inventory=True,
) -> Generator[Item, Any, None]:
    for item in room.items:
        yield item

        if include_item_inventory:
            yield from list_items_in_container(item)

    if include_character_inventory:
        for character in room.characters:
            for item in character.items:
                yield item
