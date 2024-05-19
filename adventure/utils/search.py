from typing import Any, Generator

from adventure.models.entity import Actor, Item, Portal, Room, World

from .string import normalize_name


def find_room(world: World, room_name: str) -> Room | None:
    for room in world.rooms:
        if normalize_name(room.name) == normalize_name(room_name):
            return room

    return None


def find_actor(world: World, actor_name: str) -> Actor | None:
    for room in world.rooms:
        actor = find_actor_in_room(room, actor_name)
        if actor:
            return actor

    return None


def find_actor_in_room(room: Room, actor_name: str) -> Actor | None:
    for actor in room.actors:
        if normalize_name(actor.name) == normalize_name(actor_name):
            return actor

    return None


def find_item(
    world: World,
    item_name: str,
    include_actor_inventory=False,
    include_item_inventory=False,
) -> Item | None:
    for room in world.rooms:
        item = find_item_in_room(
            room, item_name, include_actor_inventory, include_item_inventory
        )
        if item:
            return item

    return None


def find_item_in_actor(
    actor: Actor, item_name: str, include_item_inventory=False
) -> Item | None:
    for item in actor.items:
        if normalize_name(item.name) == normalize_name(item_name):
            return item

        if include_item_inventory:
            item = find_item_in_container(item, item_name, include_item_inventory)
            if item:
                return item

    return None


def find_item_in_container(
    container: Item, item_name: str, include_item_inventory=False
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
    include_actor_inventory=False,
    include_item_inventory=False,
) -> Item | None:
    for item in room.items:
        if normalize_name(item.name) == normalize_name(item_name):
            return item

        if include_item_inventory:
            item = find_item_in_container(item, item_name, include_item_inventory)
            if item:
                return item

    if include_actor_inventory:
        for actor in room.actors:
            item = find_item_in_actor(actor, item_name, include_item_inventory)
            if item:
                return item

    return None


def find_room_with_actor(world: World, actor: Actor) -> Room | None:
    for room in world.rooms:
        for room_actor in room.actors:
            if normalize_name(actor.name) == normalize_name(room_actor.name):
                return room

    return None


def find_containing_room(world: World, entity: Room | Actor | Item) -> Room | None:
    if isinstance(entity, Room):
        return entity

    for room in world.rooms:
        if entity in room.actors or entity in room.items:
            return room

    return None


def list_rooms(world: World) -> Generator[Room, Any, None]:
    for room in world.rooms:
        yield room


def list_portals(world: World) -> Generator[Portal, Any, None]:
    for room in world.rooms:
        for portal in room.portals:
            yield portal


def list_actors(world: World) -> Generator[Actor, Any, None]:
    for room in world.rooms:
        for actor in room.actors:
            yield actor


def list_items(
    world: World, include_actor_inventory=True, include_item_inventory=True
) -> Generator[Item, Any, None]:

    for room in world.rooms:
        for item in room.items:
            yield item

            if include_item_inventory:
                yield from list_items_in_container(item)

        if include_actor_inventory:
            for actor in room.actors:
                for item in actor.items:
                    yield item


def list_actors_in_room(room: Room) -> Generator[Actor, Any, None]:
    for actor in room.actors:
        yield actor


def list_items_in_actor(
    actor: Actor, include_item_inventory=True
) -> Generator[Item, Any, None]:
    for item in actor.items:
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
    include_actor_inventory=True,
    include_item_inventory=True,
) -> Generator[Item, Any, None]:
    for item in room.items:
        yield item

        if include_item_inventory:
            yield from list_items_in_container(item)

    if include_actor_inventory:
        for actor in room.actors:
            for item in actor.items:
                yield item
