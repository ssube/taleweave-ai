from logging import getLogger
from random import choice, randint
from typing import List

from packit.agent import Agent
from packit.loops import loop_retry

from adventure.models.entity import Actor, Item, Room, World, WorldEntity
from adventure.models.event import EventCallback, GenerateEvent

logger = getLogger(__name__)

OPPOSITE_DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


def duplicate_name_parser(existing_names: List[str]):
    def name_parser(name: str, **kwargs):
        if name in existing_names:
            raise ValueError(f'"{name}" has already been used.')

        if '"' in name or ":" in name:
            raise ValueError("The name cannot contain quotes or colons.")

        if len(name) > 50:
            raise ValueError("The name cannot be longer than 50 characters.")

        return name

    return name_parser


def callback_wrapper(
    callback: EventCallback | None,
    message: str | None = None,
    entity: WorldEntity | None = None,
):
    if message:
        event = GenerateEvent.from_name(message)
    elif entity:
        event = GenerateEvent.from_entity(entity)
    else:
        raise ValueError("Either message or entity must be provided")

    if callable(callback):
        callback(event)


def generate_room(
    agent: Agent,
    world_theme: str,
    callback: EventCallback | None = None,
    existing_rooms: List[str] = [],
) -> Room:
    name = loop_retry(
        agent,
        "Generate one room, area, or location that would make sense in the world of {world_theme}. "
        "Only respond with the room name in title case, do not include the description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. The existing rooms are: {existing_rooms}',
        context={
            "world_theme": world_theme,
            "existing_rooms": existing_rooms,
        },
        result_parser=duplicate_name_parser(existing_rooms),
    )

    callback_wrapper(callback, message=f"Generating room: {name}")
    desc = agent(
        "Generate a detailed description of the {name} area. What does it look like? "
        "What does it smell like? What can be seen or heard?",
        name=name,
    )

    items = []
    actors = []
    actions = {}

    return Room(
        name=name, description=desc, items=items, actors=actors, actions=actions
    )


def generate_item(
    agent: Agent,
    world_theme: str,
    callback: EventCallback | None = None,
    dest_room: str | None = None,
    dest_actor: str | None = None,
    existing_items: List[str] = [],
) -> Item:
    if dest_actor:
        dest_note = f"The item will be held by the {dest_actor} character"
    elif dest_room:
        dest_note = f"The item will be placed in the {dest_room} room"
    else:
        dest_note = "The item will be placed in the world"

    name = loop_retry(
        agent,
        "Generate one item or object that would make sense in the world of {world_theme}. {dest_note}. "
        "Only respond with the item name in title case, do not include a description or any other text. Do not prefix the "
        'name with "the", do not wrap it in quotes. Do not include the name of the room. Use a unique name. '
        "Do not create any duplicate items in the same room. Do not give characters any duplicate items. "
        "The existing items are: {existing_items}",
        context={
            "dest_note": dest_note,
            "existing_items": existing_items,
            "world_theme": world_theme,
        },
        result_parser=duplicate_name_parser(existing_items),
    )

    callback_wrapper(callback, message=f"Generating item: {name}")
    desc = agent(
        "Generate a detailed description of the {name} item. What does it look like? What is it made of? What does it do?",
        name=name,
    )

    actions = {}

    return Item(name=name, description=desc, actions=actions)


def generate_actor(
    agent: Agent,
    world_theme: str,
    dest_room: str,
    callback: EventCallback | None = None,
    existing_actors: List[str] = [],
) -> Actor:
    name = loop_retry(
        agent,
        "Generate one person or creature that would make sense in the world of {world_theme}. "
        "The character will be placed in the {dest_room} room. "
        "Only respond with the character name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. '
        "Do not include the name of the room. Do not give characters any duplicate names."
        "Do not create any duplicate characters. The existing characters are: {existing_actors}",
        context={
            "dest_room": dest_room,
            "existing_actors": existing_actors,
            "world_theme": world_theme,
        },
        result_parser=duplicate_name_parser(existing_actors),
    )

    callback_wrapper(callback, message=f"Generating actor: {name}")
    description = agent(
        "Generate a detailed description of the {name} character. What do they look like? What are they wearing? "
        "What are they doing? Describe their appearance from the perspective of an outside observer."
        "Do not include the room or any other characters in the description, because they will move around.",
        name=name,
    )
    backstory = agent(
        "Generate a backstory for the {name} actor. Where are they from? What are they doing here? What are their "
        'goals? Make sure to phrase the backstory in the second person, starting with "you are" and speaking directly to {name}.',
        name=name,
    )

    return Actor(
        name=name,
        backstory=backstory,
        description=description,
        actions={},
    )


def generate_world(
    agent: Agent,
    name: str,
    theme: str,
    room_count: int | None = None,
    max_rooms: int = 5,
    callback: EventCallback | None = None,
) -> World:
    room_count = room_count or randint(3, max_rooms)

    callback_wrapper(callback, message=f"Generating a {theme} with {room_count} rooms")

    existing_actors: List[str] = []
    existing_items: List[str] = []
    existing_rooms: List[str] = []

    # generate the rooms
    rooms = []
    for i in range(room_count):
        try:
            room = generate_room(
                agent, theme, existing_rooms=existing_rooms, callback=callback
            )
            callback_wrapper(callback, entity=room)
            rooms.append(room)
            existing_rooms.append(room.name)
        except Exception:
            logger.exception("error generating room")
            continue

        item_count = randint(1, 3)
        callback_wrapper(
            callback, f"Generating {item_count} items for room: {room.name}"
        )

        for j in range(item_count):
            try:
                item = generate_item(
                    agent,
                    theme,
                    dest_room=room.name,
                    existing_items=existing_items,
                    callback=callback,
                )
                callback_wrapper(callback, entity=item)

                room.items.append(item)
                existing_items.append(item.name)
            except Exception:
                logger.exception("error generating item")

        actor_count = randint(1, 3)
        callback_wrapper(
            callback, message=f"Generating {actor_count} actors for room: {room.name}"
        )

        for j in range(actor_count):
            try:
                actor = generate_actor(
                    agent,
                    theme,
                    dest_room=room.name,
                    existing_actors=existing_actors,
                    callback=callback,
                )
                callback_wrapper(callback, entity=actor)

                room.actors.append(actor)
                existing_actors.append(actor.name)
            except Exception:
                logger.exception("error generating actor")
                continue

            # generate the actor's inventory
            item_count = randint(0, 2)
            callback_wrapper(
                callback, f"Generating {item_count} items for actor {actor.name}"
            )

            for k in range(item_count):
                try:
                    item = generate_item(
                        agent,
                        theme,
                        dest_room=room.name,
                        existing_items=existing_items,
                        callback=callback,
                    )
                    callback_wrapper(callback, entity=item)

                    actor.items.append(item)
                    existing_items.append(item.name)
                except Exception:
                    logger.exception("error generating item")

    # generate portals to link the rooms together
    for room in rooms:
        directions = ["north", "south", "east", "west"]
        for direction in directions:
            if direction in room.portals:
                logger.debug(f"Room {room.name} already has a {direction} portal")
                continue

            opposite_direction = OPPOSITE_DIRECTIONS[direction]

            if randint(0, 1):
                dest_room = choice([r for r in rooms if r.name != room.name])

                # make sure not to create duplicate links
                if room.name in dest_room.portals.values():
                    logger.debug(
                        f"Room {dest_room.name} already has a portal to {room.name}"
                    )
                    continue

                if opposite_direction in dest_room.portals:
                    logger.debug(
                        f"Room {dest_room.name} already has a {opposite_direction} portal"
                    )
                    continue

                # create bidirectional links
                room.portals[direction] = dest_room.name
                dest_room.portals[OPPOSITE_DIRECTIONS[direction]] = room.name

    # ensure actors act in a stable order
    order = [actor.name for room in rooms for actor in room.actors]
    return World(name=name, rooms=rooms, theme=theme, order=order)
