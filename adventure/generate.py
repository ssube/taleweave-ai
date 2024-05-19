from logging import getLogger
from random import choice, randint
from typing import List, Tuple

from packit.agent import Agent
from packit.loops import loop_retry
from packit.utils import could_be_json

from adventure.context import broadcast
from adventure.game_system import GameSystem
from adventure.models.config import DEFAULT_CONFIG, WorldConfig
from adventure.models.entity import (
    Actor,
    Effect,
    Item,
    NumberAttributeEffect,
    Portal,
    Room,
    StringAttributeEffect,
    World,
    WorldEntity,
)
from adventure.models.event import GenerateEvent

logger = getLogger(__name__)

world_config: WorldConfig = DEFAULT_CONFIG.world


def duplicate_name_parser(existing_names: List[str]):
    def name_parser(value: str, **kwargs):
        logger.debug(f"validating generated name: {value}")

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


def broadcast_generated(
    message: str | None = None,
    entity: WorldEntity | None = None,
):
    if message:
        event = GenerateEvent.from_name(message)
    elif entity:
        event = GenerateEvent.from_entity(entity)
    else:
        raise ValueError("Either message or entity must be provided")

    broadcast(event)


def generate_room(
    agent: Agent,
    world_theme: str,
    existing_rooms: List[str] = [],
    systems: List[GameSystem] = [],
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

    broadcast_generated(message=f"Generating room: {name}")
    desc = agent(
        "Generate a detailed description of the {name} area. What does it look like? "
        "What does it smell like? What can be seen or heard?",
        name=name,
    )

    actions = {}

    item_count = randint(
        world_config.size.room_items.min, world_config.size.room_items.max
    )
    broadcast_generated(f"Generating {item_count} items for room: {name}")

    items = []
    for j in range(item_count):
        existing_items = [item.name for item in items]

        try:
            item = generate_item(
                agent,
                world_theme,
                dest_room=name,
                existing_items=existing_items,
            )
            generate_system_attributes(agent, world_theme, item, systems)
            broadcast_generated(entity=item)

            items.append(item)
        except Exception:
            logger.exception("error generating item")

    actor_count = randint(
        world_config.size.room_actors.min, world_config.size.room_actors.max
    )
    broadcast_generated(message=f"Generating {actor_count} actors for room: {name}")

    actors = []
    for j in range(actor_count):
        existing_actors = [actor.name for actor in actors]

        try:
            actor = generate_actor(
                agent,
                world_theme,
                dest_room=name,
                existing_actors=existing_actors,
            )
            generate_system_attributes(agent, world_theme, actor, systems)
            broadcast_generated(entity=actor)

            actors.append(actor)
        except Exception:
            logger.exception("error generating actor")
            continue

    return Room(
        name=name, description=desc, items=items, actors=actors, actions=actions
    )


def generate_portals(
    agent: Agent,
    world_theme: str,
    source_room: Room,
    dest_room: Room,
) -> Tuple[Portal, Portal]:
    existing_source_portals = [portal.name for portal in source_room.portals]
    existing_dest_portals = [portal.name for portal in dest_room.portals]

    outgoing_name = loop_retry(
        agent,
        "Generate the name of a portal that leads from the {source_room} room to the {dest_room} room and fits the world theme of {world_theme}. "
        "Some example portal names are: 'door', 'gate', 'archway', 'staircase', 'trapdoor', 'mirror', and 'magic circle'. "
        "Only respond with the portal name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. Use a unique name. '
        "Do not create any duplicate portals in the same room. The existing portals are: {existing_portals}",
        context={
            "source_room": source_room.name,
            "dest_room": dest_room.name,
            "existing_portals": existing_source_portals,
            "world_theme": world_theme,
        },
        result_parser=duplicate_name_parser(existing_source_portals),
    )
    broadcast_generated(message=f"Generating portal: {outgoing_name}")

    incoming_name = loop_retry(
        agent,
        "Generate the opposite name of the portal that leads from the {dest_room} room to the {source_room} room. "
        "The name should be the opposite of the {outgoing_name} portal and should fit the world theme of {world_theme}. "
        "Some example portal names are: 'door', 'gate', 'archway', 'staircase', 'trapdoor', 'mirror', and 'magic circle'. "
        "Only respond with the portal name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. Use a unique name. '
        "Do not create any duplicate portals in the same room. The existing portals are: {existing_portals}",
        context={
            "source_room": source_room.name,
            "dest_room": dest_room.name,
            "existing_portals": existing_dest_portals,
            "world_theme": world_theme,
            "outgoing_name": outgoing_name,
        },
        result_parser=duplicate_name_parser(existing_dest_portals),
    )

    broadcast_generated(message=f"Linking {outgoing_name} to {incoming_name}")

    outgoing_portal = Portal(
        name=outgoing_name,
        description=f"A {outgoing_name} leads to the {dest_room.name} room.",
        destination=dest_room.name,
    )
    incoming_portal = Portal(
        name=incoming_name,
        description=f"A {incoming_name} leads to the {source_room.name} room.",
        destination=source_room.name,
    )

    return (outgoing_portal, incoming_portal)


def generate_item(
    agent: Agent,
    world_theme: str,
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

    broadcast_generated(message=f"Generating item: {name}")
    desc = agent(
        "Generate a detailed description of the {name} item. What does it look like? What is it made of? What does it do?",
        name=name,
    )

    actions = {}
    item = Item(name=name, description=desc, actions=actions)

    effect_count = randint(
        world_config.size.item_effects.min, world_config.size.item_effects.max
    )
    broadcast_generated(message=f"Generating {effect_count} effects for item: {name}")

    effects = []
    for i in range(effect_count):
        existing_effects = [effect.name for effect in effects]

        try:
            effect = generate_effect(
                agent, world_theme, entity=item, existing_effects=existing_effects
            )
            effects.append(effect)
        except Exception:
            logger.exception("error generating effect")

    item.effects = effects
    return item


def generate_actor(
    agent: Agent,
    world_theme: str,
    dest_room: str,
    existing_actors: List[str] = [],
    systems: List[GameSystem] = [],
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

    broadcast_generated(message=f"Generating actor: {name}")
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

    # generate the actor's inventory
    item_count = randint(
        world_config.size.actor_items.min, world_config.size.actor_items.max
    )
    broadcast_generated(f"Generating {item_count} items for actor {name}")

    items = []
    for k in range(item_count):
        existing_items = [item.name for item in items]

        try:
            item = generate_item(
                agent,
                world_theme,
                dest_actor=name,
                existing_items=existing_items,
            )
            generate_system_attributes(agent, world_theme, item, systems)
            broadcast_generated(entity=item)

            items.append(item)
        except Exception:
            logger.exception("error generating item")

    return Actor(
        name=name,
        backstory=backstory,
        description=description,
        actions={},
        items=items,
    )


# TODO: move to utils
def try_parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


# TODO: move to utils
def try_parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def generate_effect(
    agent: Agent, theme: str, entity: Item, existing_effects: List[str] = []
) -> Effect:
    entity_type = entity.type

    name = loop_retry(
        agent,
        "Generate one effect for an {entity_type} named {entity_name} that would make sense in the world of {theme}. "
        "Only respond with the effect name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. Use a unique name. '
        "Do not create any duplicate effects on the same item. The existing effects are: {existing_effects}. "
        "Some example effects are: 'fire', 'poison', 'frost', 'haste', 'slow', and 'heal'.",
        context={
            "entity_name": entity.name,
            "entity_type": entity_type,
            "existing_effects": existing_effects,
            "theme": theme,
        },
        result_parser=duplicate_name_parser(existing_effects),
    )
    broadcast_generated(message=f"Generating effect: {name}")

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
                "Reply with the operation only, without any other text. Give a single word."
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

            PROMPT_TYPE_FRAGMENTS = {
                "both": "Enter a positive or negative number, or a string value",
                "number": "Enter a positive or negative number",
                "string": "Enter a string value",
            }

            PROMPT_OPERATION_TYPES = {
                "set": "both",
                "add": "number",
                "subtract": "number",
                "multiply": "number",
                "divide": "number",
                "append": "string",
                "prepend": "string",
            }

            operation_type = PROMPT_OPERATION_TYPES[operation]
            operation_prompt = PROMPT_TYPE_FRAGMENTS[operation_type]

            value = agent(
                f"How much does the {name} effect modify the {attribute_name} attribute? "
                "For example, heal might add '10' to the health attribute, while poison might subtract '5' from it."
                f"{operation_prompt}. Do not include any other text. Do not use JSON.",
                name=name,
                attribute_name=attribute_name,
            )
            value = value.strip()

            int_value = try_parse_int(value)
            if int_value is not None:
                attribute_effect = NumberAttributeEffect(
                    name=attribute_name, operation=operation, value=int_value
                )
            else:
                float_value = try_parse_float(value)
                if float_value is not None:
                    attribute_effect = NumberAttributeEffect(
                        name=attribute_name, operation=operation, value=float_value
                    )
                else:
                    attribute_effect = StringAttributeEffect(
                        name=attribute_name, operation=operation, value=value
                    )

            attributes.append(attribute_effect)

    return Effect(name=name, description=description, attributes=attributes)


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
    systems: List[GameSystem] = [],
) -> World:
    room_count = room_count or randint(
        world_config.size.rooms.min, world_config.size.rooms.max
    )

    broadcast_generated(message=f"Generating a {theme} with {room_count} rooms")

    # generate the rooms
    rooms = []
    for i in range(room_count):
        existing_rooms = [room.name for room in rooms]

        try:
            room = generate_room(agent, theme, existing_rooms=existing_rooms)
            generate_system_attributes(agent, theme, room, systems)
            broadcast_generated(entity=room)
            rooms.append(room)
        except Exception:
            logger.exception("error generating room")
            continue

    # generate portals to link the rooms together
    for room in rooms:
        num_portals = randint(
            world_config.size.portals.min, world_config.size.portals.max
        )

        if len(room.portals) >= num_portals:
            logger.info(f"room {room.name} already has enough portals")
            continue

        broadcast_generated(
            message=f"Generating {num_portals} portals for room: {room.name}"
        )

        for i in range(num_portals):
            previous_destinations = [portal.destination for portal in room.portals] + [
                room.name
            ]
            remaining_rooms = [r for r in rooms if r.name not in previous_destinations]
            if len(remaining_rooms) == 0:
                logger.info(f"no more rooms to link to from {room.name}")
                break

            # TODO: prompt the DM to choose a destination room
            dest_room = choice(
                [r for r in rooms if r.name not in previous_destinations]
            )

            try:
                outgoing_portal, incoming_portal = generate_portals(
                    agent, theme, room, dest_room
                )

                room.portals.append(outgoing_portal)
                dest_room.portals.append(incoming_portal)
            except Exception:
                logger.exception("error generating portal")
                continue

    # ensure actors act in a stable order
    order = [actor.name for room in rooms for actor in room.actors]
    return World(name=name, rooms=rooms, theme=theme, order=order)
