from logging import getLogger
from random import choice, randint
from typing import List

from packit.agent import Agent
from packit.loops import loop_retry
from packit.utils import could_be_json

from adventure.game_system import GameSystem
from adventure.models.entity import (
    Actor,
    Effect,
    Item,
    NumberAttributeEffect,
    Room,
    StringAttributeEffect,
    World,
    WorldEntity,
)
from adventure.models.event import EventCallback, GenerateEvent

logger = getLogger(__name__)

OPPOSITE_DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


def duplicate_name_parser(existing_names: List[str]):
    def name_parser(value: str, **kwargs):
        print(f"validating generated name: {value}")

        if value in existing_names:
            raise ValueError(f'"{value}" has already been used.')

        if could_be_json(value):
            raise ValueError("The name cannot contain JSON or other commands.")

        if '"' in value or ":" in value:
            raise ValueError("The name cannot contain quotes or colons.")

        if len(value) > 50:
            raise ValueError("The name cannot be longer than 50 characters.")

        return value

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
    item = Item(name=name, description=desc, actions=actions)

    effect_count = randint(1, 2)
    callback_wrapper(
        callback, message=f"Generating {effect_count} effects for item: {name}"
    )

    effects = []
    for i in range(effect_count):
        try:
            effect = generate_effect(agent, world_theme, entity=item, callback=callback)
            effects.append(effect)
        except Exception:
            logger.exception("error generating effect")

    item.effects = effects
    return item


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


def generate_effect(
    agent: Agent, theme: str, entity: Item, callback: EventCallback | None = None
) -> Effect:
    entity_type = entity.type

    existing_effects = [effect.name for effect in entity.effects]

    name = loop_retry(
        agent,
        "Generate one effect for an {entity_type} named {entity.name} that would make sense in the world of {theme}. "
        "Only respond with the effect name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. Use a unique name. '
        "Do not create any duplicate effects on the same item. The existing effects are: {existing_effects}. "
        "Some example effects are: 'fire', 'poison', 'frost', 'haste', 'slow', and 'heal'.",
        context={
            "entity_type": entity_type,
            "existing_effects": existing_effects,
            "theme": theme,
        },
        result_parser=duplicate_name_parser(existing_effects),
    )
    callback_wrapper(callback, message=f"Generating effect: {name}")

    description = agent(
        "Generate a detailed description of the {name} effect. What does it look like? What does it do? "
        "How does it affect the target? Describe the effect from the perspective of an outside observer.",
        name=name,
    )

    attribute_names = agent(
        "Generate a list of attributes that the {name} effect modifies. "
        "For example, 'heal' increases the target's 'health' attribute, while 'poison' decreases it. "
        "Use a comma-separated list of attribute names, such as 'health, strength, speed'. "
        "Only include the attribute names, do not include the question or any JSON.",
        name=name,
    )

    attributes = []
    for attribute_name in attribute_names.split(","):
        attribute_name = attribute_name.strip()
        if attribute_name:
            operation = agent(
                f"How does the {name} effect modify the {attribute_name} attribute? "
                "For example, 'heal' might 'add' to the 'health' attribute, while 'poison' might 'subtract' from it."
                "Another example is 'writing' might 'set' the 'text' attribute, while 'break' might 'set' the 'condition' attribute."
                "Choose from the following operations: {operations}",
                name=name,
                attribute_name=attribute_name,
                operations=[
                    "set",
                    "add",
                    "subtract",
                    "multiply",
                    "divide",
                    "append",
                    "prepend",
                ],
            )
            value = agent(
                f"How much does the {name} effect modify the {attribute_name} attribute? "
                "For example, 'heal' might 'add' 10 to the 'health' attribute, while 'poison' might 'subtract' 5 from it."
                "Enter a positive or negative number, or a string value.",
                name=name,
                attribute_name=attribute_name,
            )
            value = value.strip()
            if value.isdigit():
                value = int(value)
                attribute_effect = NumberAttributeEffect(
                    name=attribute_name, operation=operation, value=value
                )
            elif value.isdecimal():
                value = float(value)
                attribute_effect = NumberAttributeEffect(
                    name=attribute_name, operation=operation, value=value
                )
            else:
                attribute_effect = StringAttributeEffect(
                    name=attribute_name, operation=operation, value=value
                )

            attributes.append(attribute_effect)

    return Effect(name=name, description=description, attributes=[])


def generate_system_attributes(
    agent: Agent, theme: str, entity: WorldEntity, systems: List[GameSystem] = []
) -> None:
    for system in systems:
        if system.generate:
            system.generate(agent, theme, entity)


def generate_world(
    agent: Agent,
    name: str,
    theme: str,
    room_count: int | None = None,
    max_rooms: int = 5,
    callback: EventCallback | None = None,
    systems: List[GameSystem] = [],
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
            generate_system_attributes(agent, theme, room, systems)
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
                generate_system_attributes(agent, theme, item, systems)
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
                generate_system_attributes(agent, theme, actor, systems)
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
                    generate_system_attributes(agent, theme, item, systems)
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
