from logging import getLogger
from random import choice
from typing import List, Tuple

from packit.agent import Agent
from packit.loops import loop_retry
from packit.results import enum_result, int_result
from packit.utils import could_be_json

from taleweave.context import broadcast, set_current_world, set_system_data
from taleweave.game_system import GameSystem
from taleweave.models.config import DEFAULT_CONFIG, WorldConfig
from taleweave.models.effect import (
    EffectPattern,
    FloatEffectPattern,
    IntEffectPattern,
    StringEffectPattern,
)
from taleweave.models.entity import Character, Item, Portal, Room, World, WorldEntity
from taleweave.models.event import GenerateEvent
from taleweave.utils import try_parse_float, try_parse_int
from taleweave.utils.effect import resolve_int_range
from taleweave.utils.search import (
    list_characters,
    list_characters_in_room,
    list_items,
    list_items_in_character,
    list_items_in_room,
    list_rooms,
)
from taleweave.utils.string import normalize_name

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


def generate_system_attributes(
    agent: Agent, world: World, entity: WorldEntity, systems: List[GameSystem]
) -> None:
    for system in systems:
        if system.generate:
            # TODO: pass the whole world
            system.generate(agent, world.theme, entity)


def generate_room(
    agent: Agent,
    world: World,
    systems: List[GameSystem],
) -> Room:
    existing_rooms = [room.name for room in list_rooms(world)]

    name = loop_retry(
        agent,
        "Generate one room, area, or location that would make sense in the world of {world_theme}. "
        "Only respond with the room name in title case, do not include the description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. The existing rooms are: {existing_rooms}',
        context={
            "world_theme": world.theme,
            "existing_rooms": existing_rooms,
        },
        result_parser=duplicate_name_parser(existing_rooms),
        toolbox=None,
    )

    broadcast_generated(message=f"Generating room: {name}")
    desc = agent(
        "Generate a detailed description of the {name} area. What does it look like? "
        "What does it smell like? What can be seen or heard?",
        name=name,
    )

    actions = {}
    room = Room(name=name, description=desc, items=[], characters=[], actions=actions)

    item_count = resolve_int_range(world_config.size.room_items) or 0
    broadcast_generated(f"Generating {item_count} items for room: {name}")

    for _ in range(item_count):
        try:
            item = generate_item(
                agent,
                world,
                systems=systems,
                dest_room=room,
            )
            broadcast_generated(entity=item)

            room.items.append(item)
        except Exception:
            logger.exception("error generating item")

    character_count = resolve_int_range(world_config.size.room_characters) or 0
    broadcast_generated(
        message=f"Generating {character_count} characters for room: {name}"
    )

    for _ in range(character_count):
        try:
            character = generate_character(
                agent,
                world,
                systems=systems,
                dest_room=room,
            )
            broadcast_generated(entity=character)

            room.characters.append(character)
        except Exception:
            logger.exception("error generating character")
            continue

    return room


def generate_portals(
    agent: Agent,
    world: World,
    source_room: Room,
    dest_room: Room,
    systems: List[GameSystem],
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
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_source_portals),
        toolbox=None,
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
            "world_theme": world.theme,
            "outgoing_name": outgoing_name,
        },
        result_parser=duplicate_name_parser(existing_dest_portals),
        toolbox=None,
    )

    broadcast_generated(message=f"Linking {outgoing_name} to {incoming_name}")

    outgoing_portal = Portal(
        name=outgoing_name,
        description=f"A {outgoing_name} leads to the {dest_room.name} room.",
        destination=dest_room.name,
    )
    generate_system_attributes(agent, world, outgoing_portal, systems)

    incoming_portal = Portal(
        name=incoming_name,
        description=f"A {incoming_name} leads to the {source_room.name} room.",
        destination=source_room.name,
    )
    generate_system_attributes(agent, world, incoming_portal, systems)

    return (outgoing_portal, incoming_portal)


def generate_item(
    agent: Agent,
    world: World,
    systems: List[GameSystem],
    dest_room: Room | None = None,
    dest_character: Character | None = None,
) -> Item:
    existing_items = [
        item.name
        for item in list_items(
            world, include_character_inventory=True, include_item_inventory=True
        )
    ]

    if dest_character:
        dest_note = f"The item will be held by the {dest_character.name} character"
        existing_items += [
            item.name for item in list_items_in_character(dest_character)
        ]
    elif dest_room:
        dest_note = f"The item will be placed in the {dest_room.name} room"
        existing_items += [item.name for item in list_items_in_room(dest_room)]
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
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_items),
        toolbox=None,
    )

    broadcast_generated(message=f"Generating item: {name}")
    desc = agent(
        "Generate a detailed description of the {name} item. What does it look like? What is it made of? What does it do?",
        name=name,
    )

    actions = {}
    item = Item(name=name, description=desc, actions=actions)
    generate_system_attributes(agent, world, item, systems)

    effect_count = resolve_int_range(world_config.size.item_effects) or 0
    broadcast_generated(message=f"Generating {effect_count} effects for item: {name}")

    for _ in range(effect_count):
        try:
            effect = generate_effect(agent, world, entity=item)
            item.effects.append(effect)
        except Exception:
            logger.exception("error generating effect")

    return item


def generate_character(
    agent: Agent,
    world: World,
    systems: List[GameSystem],
    dest_room: Room,
    additional_prompt: str = "",
    detail_prompt: str = "",
    add_to_world_order: bool = True,
) -> Character:
    existing_characters = [character.name for character in list_characters(world)] + [
        character.name for character in list_characters_in_room(dest_room)
    ]

    name = loop_retry(
        agent,
        "Generate a new character that would make sense in the world of {world_theme}. Characters can be a person, creature, or some other intelligent entity."
        "The character will be placed in the {dest_room} room. {additional_prompt}. "
        "Only respond with the character name in title case, do not include a description or any other text. "
        'Do not prefix the name with "the", do not wrap it in quotes. '
        "Do not include the name of the room. Do not give characters any duplicate names."
        "Do not create any duplicate characters. The existing characters are: {existing_characters}",
        context={
            "additional_prompt": additional_prompt,
            "dest_room": dest_room.name,
            "existing_characters": existing_characters,
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_characters),
        toolbox=None,
    )

    broadcast_generated(message=f"Generating character: {name}")
    description = agent(
        "Generate a detailed description of the {name} character. {additional_prompt}. {detail_prompt}. What do they look like? What are they wearing? "
        "What are they doing? Describe their appearance from the perspective of an outside observer."
        "Do not include the room or any other characters in the description, because they will move around.",
        additional_prompt=additional_prompt,
        detail_prompt=detail_prompt,
        name=name,
    )
    backstory = agent(
        "Generate a backstory for the {name} character. {additional_prompt}. {detail_prompt}. Where are they from? What are they doing here? What are their "
        'goals? Make sure to phrase the backstory in the second person, starting with "you are" and speaking directly to {name}.',
        additional_prompt=additional_prompt,
        detail_prompt=detail_prompt,
        name=name,
    )

    character = Character(
        name=name, backstory=backstory, description=description, actions={}, items=[]
    )
    generate_system_attributes(agent, world, character, systems)

    # generate the character's inventory
    item_count = resolve_int_range(world_config.size.character_items) or 0
    broadcast_generated(f"Generating {item_count} items for character {name}")

    for k in range(item_count):
        try:
            item = generate_item(
                agent,
                world,
                systems,
                dest_character=character,
            )
            generate_system_attributes(agent, world, item, systems)
            broadcast_generated(entity=item)

            character.items.append(item)
        except Exception:
            logger.exception("error generating item")

    if add_to_world_order:
        logger.info(f"adding character {name} to end of world turn order")
        world.order.append(name)

    return character


def generate_effect(agent: Agent, world: World, entity: Item) -> EffectPattern:
    entity_type = entity.type
    existing_effects = [effect.name for effect in entity.effects]

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
            "theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_effects),
        toolbox=None,
    )
    broadcast_generated(message=f"Generating effect: {name}")

    description = agent(
        "Generate a detailed description of the {name} effect. What does it look like? What does it do? "
        "How does it affect the target? Describe the effect from the perspective of an outside observer.",
        name=name,
    )

    cooldown = loop_retry(
        agent,
        f"How many turns should the {name} effect wait before it can be used again? Enter a positive number to set a cooldown, or 0 for no cooldown. "
        "Do not include any other text. Do not use JSON.",
        context={
            "name": name,
        },
        result_parser=int_result,
        toolbox=None,
    )

    uses = loop_retry(
        agent,
        f"How many times can the {name} effect be used before it is exhausted? Enter a positive number to set a limit, or -1 for unlimited uses. "
        "Do not include any other text. Do not use JSON.",
        context={
            "name": name,
        },
        result_parser=int_result,
        toolbox=None,
    )

    if uses == -1:
        uses = None

    attribute_names = agent(
        "Generate a short list of attributes that the {name} effect modifies. Include 1 to 3 attributes. "
        "For example, 'heal' increases the target's 'health' attribute, while 'poison' decreases it. "
        "Use a comma-separated list of attribute names, such as 'health, strength, speed'. "
        "Only include the attribute names, do not include the question or any JSON.",
        name=name,
    )

    attributes = []
    for attribute_name in attribute_names.split(","):
        attribute_name = normalize_name(attribute_name)
        if attribute_name:
            value = agent(
                f"How much does the {name} effect modify the {attribute_name} attribute? "
                "For example, heal might add 10 to the health attribute, while poison might remove -5 from it."
                "Enter a positive number to increase the attribute or a negative number to decrease it. "
                "Do not include any other text. Do not use JSON.",
                name=name,
                attribute_name=attribute_name,
            )
            value = value.strip()

            # TODO: support more than just set: offset and multiply
            int_value = try_parse_int(value)
            if int_value is not None:
                attribute_effect = IntEffectPattern(name=attribute_name, set=int_value)
            else:
                float_value = try_parse_float(value)
                if float_value is not None:
                    attribute_effect = FloatEffectPattern(
                        name=attribute_name, set=float_value
                    )
                else:
                    attribute_effect = StringEffectPattern(
                        name=attribute_name, set=value
                    )

            attributes.append(attribute_effect)

    duration = loop_retry(
        agent,
        f"How many turns does the {name} effect last? Enter a positive number to set a duration, or 0 for an instant effect. "
        "Do not include any other text. Do not use JSON.",
        context={
            "name": name,
        },
        result_parser=int_result,
        toolbox=None,
    )

    def parse_application(value: str, **kwargs) -> str:
        value = enum_result(value, ["temporary", "permanent"])
        if value:
            return value

        raise ValueError("The application must be 'temporary' or 'permanent'.")

    application = loop_retry(
        agent,
        (
            f"How should the {name} effect be applied? Respond with 'temporary' for a temporary effect that lasts for a duration, "
            "or 'permanent' for a permanent effect that immediately modifies the target. "
            "For example, a healing potion would be a permanent effect that increases health every turn, "
            "while bleeding would be a temporary effect that decreases health every turn. "
            "A haste potion would be a temporary effect that increases speed for a duration, "
            "while a slow spell would be a temporary effect that decreases speed for a duration. "
            "Do not include any other text. Do not use JSON."
        ),
        context={
            "name": name,
        },
        result_parser=parse_application,
        toolbox=None,
    )

    return EffectPattern(
        name,
        description,
        application,
        attributes=attributes,
        cooldown=cooldown,
        duration=duration,
        uses=uses,
    )


def link_rooms(
    agent: Agent,
    world: World,
    systems: List[GameSystem],
    rooms: List[Room] | None = None,
) -> None:
    rooms = rooms or world.rooms

    for room in rooms:
        num_portals = resolve_int_range(world_config.size.portals) or 0

        if len(room.portals) >= num_portals:
            logger.info(f"room {room.name} already has enough portals")
            continue

        broadcast_generated(
            message=f"Generating {num_portals} portals for room: {room.name}"
        )

        for _ in range(num_portals):
            previous_destinations = [portal.destination for portal in room.portals] + [
                room.name
            ]
            remaining_rooms = [
                r for r in world.rooms if r.name not in previous_destinations
            ]
            if len(remaining_rooms) == 0:
                logger.info(f"no more rooms to link to from {room.name}")
                break

            # TODO: prompt the DM to choose a destination room
            dest_room = choice(
                [r for r in world.rooms if r.name not in previous_destinations]
            )

            try:
                outgoing_portal, incoming_portal = generate_portals(
                    agent, world, room, dest_room, systems
                )

                room.portals.append(outgoing_portal)
                dest_room.portals.append(incoming_portal)
            except Exception:
                logger.exception("error generating portal")
                continue


def generate_world(
    agent: Agent,
    name: str,
    theme: str,
    systems: List[GameSystem],
    room_count: int | None = None,
) -> World:
    room_count = room_count or resolve_int_range(world_config.size.rooms) or 0

    broadcast_generated(message=f"Generating a {theme} with {room_count} rooms")
    world = World(name=name, rooms=[], theme=theme, order=[])
    set_current_world(world)

    # initialize the systems
    for system in systems:
        if system.initialize:
            data = system.initialize(world)
            set_system_data(system.name, data)

    # generate the rooms
    for _ in range(room_count):
        try:
            room = generate_room(agent, world, systems)
            generate_system_attributes(agent, world, room, systems)
            broadcast_generated(entity=room)
            world.rooms.append(room)
        except Exception:
            logger.exception("error generating room")
            continue

    # generate portals to link the rooms together
    link_rooms(agent, world, systems)

    # ensure characters act in a stable order
    world.order = [
        character.name for room in world.rooms for character in room.characters
    ]
    return world
