from logging import getLogger
from random import choice, randint
from typing import Callable, List

from packit.agent import Agent

from adventure.models import Actor, Item, Room, World

logger = getLogger(__name__)


def generate_room(
    agent: Agent, world_theme: str, existing_rooms: List[str], callback
) -> Room:
    name = agent(
        "Generate one room, area, or location that would make sense in the world of {world_theme}. "
        "Only respond with the room name, do not include the description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. The existing rooms are: {existing_rooms}',
        world_theme=world_theme,
        existing_rooms=existing_rooms,
    )
    callback(f"Generating room: {name}")
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
    existing_items: List[str],
    callback,
    dest_room: str | None = None,
    dest_actor: str | None = None,
) -> Item:
    if dest_actor:
        dest_note = "The item will be held by the {dest_actor} character"
    elif dest_room:
        dest_note = "The item will be placed in the {dest_room} room"
    else:
        dest_note = "The item will be placed in the world"

    name = agent(
        "Generate one item or object that would make sense in the world of {world_theme}. {dest_note}. "
        "Only respond with the item name, do not include a description or any other text. Do not prefix the "
        'name with "the", do not wrap it in quotes. Do not include the name of the room. '
        "Do not create any duplicate items in the same room. Do not give characters any duplicate items. The existing items are: {existing_items}",
        dest_note=dest_note,
        existing_items=existing_items,
        world_theme=world_theme,
    )
    callback(f"Generating item: {name}")
    desc = agent(
        "Generate a detailed description of the {name} item. What does it look like? What is it made of? What does it do?",
        name=name,
    )

    actions = {}

    return Item(name=name, description=desc, actions=actions)


def generate_actor(
    agent: Agent, world_theme: str, dest_room: str, existing_actors: List[str], callback
) -> Actor:
    name = agent(
        "Generate one person or creature that would make sense in the world of {world_theme}. The character will be placed in the {dest_room} room. "
        'Only respond with the character name, do not include a description or any other text. Do not prefix the name with "the", do not wrap it in quotes. '
        "Do not include the name of the room. Do not give characters any duplicate names."
        "Do not create any duplicate characters. The existing characters are: {existing_actors}",
        dest_room=dest_room,
        existing_actors=existing_actors,
        world_theme=world_theme,
    )
    callback(f"Generating actor: {name}")
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
    callback: Callable[[str], None] = lambda x: None,
) -> World:
    room_count = room_count or randint(3, max_rooms)
    callback(f"Generating a {theme} with {room_count} rooms")

    existing_actors: List[str] = []
    existing_items: List[str] = []

    # generate the rooms
    rooms = []
    for i in range(room_count):
        existing_rooms = [room.name for room in rooms]
        room = generate_room(agent, theme, existing_rooms, callback=callback)
        rooms.append(room)

        item_count = randint(0, 3)
        callback(f"Generating {item_count} items for room {room.name}")

        for j in range(item_count):
            item = generate_item(
                agent,
                theme,
                dest_room=room.name,
                existing_items=existing_items,
                callback=callback,
            )
            room.items.append(item)
            existing_items.append(item.name)

        actor_count = randint(0, 3)
        callback(f"Generating {actor_count} actors for room {room.name}")

        for j in range(actor_count):
            actor = generate_actor(
                agent,
                theme,
                dest_room=room.name,
                existing_actors=existing_actors,
                callback=callback,
            )
            room.actors.append(actor)
            existing_actors.append(actor.name)

            # generate the actor's inventory
            item_count = randint(0, 3)
            callback(f"Generating {item_count} items for actor {actor.name}")

            for k in range(item_count):
                item = generate_item(
                    agent,
                    theme,
                    dest_room=room.name,
                    existing_items=existing_items,
                    callback=callback,
                )
                actor.items.append(item)
                existing_items.append(item.name)

    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
    }

    # generate portals to link the rooms together
    for room in rooms:
        directions = ["north", "south", "east", "west"]
        for direction in directions:
            if direction in room.portals:
                logger.debug(f"Room {room.name} already has a {direction} portal")
                continue

            opposite_direction = opposite_directions[direction]

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
                dest_room.portals[opposite_directions[direction]] = room.name

    # ensure actors act in a stable order
    order = [actor.name for room in rooms for actor in room.actors]
    return World(name=name, rooms=rooms, theme=theme, order=order)
