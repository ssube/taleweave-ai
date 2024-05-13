from adventure.models.entity import Actor, Item, Room, World


def find_room(world: World, room_name: str) -> Room | None:
    for room in world.rooms:
        if room.name.lower() == room_name.lower():
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
        if actor.name.lower() == actor_name.lower():
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
        if item.name.lower() == item_name.lower():
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
        if item.name.lower() == item_name.lower():
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
        if item.name.lower() == item_name.lower():
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
