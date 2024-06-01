from logging import getLogger
from random import choice
from typing import List, Tuple

from packit.agent import Agent
from packit.loops import loop_retry
from packit.results import enum_result, int_result
from packit.utils import could_be_json

from taleweave.context import (
    broadcast,
    get_game_config,
    get_prompt,
    set_current_world,
    set_system_data,
)
from taleweave.game_system import GameSystem
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
from taleweave.utils.prompt import format_prompt
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


def get_world_config():
    config = get_game_config()
    return config.world


def duplicate_name_parser(existing_names: List[str]):
    def name_parser(value: str, **kwargs):
        logger.debug(f"validating generated name: {value}")

        if value in existing_names:
            raise ValueError(
                format_prompt("world_generate_error_name_exists", name=value)
            )

        if could_be_json(value):
            raise ValueError(
                format_prompt("world_generate_error_name_json", name=value)
            )

        if '"' in value or ":" in value:
            raise ValueError(
                format_prompt("world_generate_error_name_punctuation", name=value)
            )

        if len(value) > 50:
            raise ValueError(
                format_prompt("world_generate_error_name_length", name=value)
            )

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
        get_prompt("world_generate_room_name"),
        context={
            "world_theme": world.theme,
            "existing_rooms": existing_rooms,
        },
        result_parser=duplicate_name_parser(existing_rooms),
        toolbox=None,
    )

    broadcast_generated(format_prompt("world_generate_room_broadcast_room", name=name))
    desc = agent(get_prompt("world_generate_room_description"), name=name)

    actions = {}
    room = Room(name=name, description=desc, items=[], characters=[], actions=actions)

    world_config = get_world_config()
    item_count = resolve_int_range(world_config.size.room_items) or 0
    broadcast_generated(
        format_prompt(
            "world_generate_room_broadcast_items", item_count=item_count, name=name
        )
    )

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
        format_prompt(
            "world_generate_room_broadcast_characters",
            character_count=character_count,
            name=name,
        )
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
    outgoing_name: str | None = None,
) -> Tuple[Portal, Portal]:
    existing_source_portals = [portal.name for portal in source_room.portals]
    existing_dest_portals = [portal.name for portal in dest_room.portals]

    outgoing_name = outgoing_name or loop_retry(
        agent,
        get_prompt("world_generate_portal_name_outgoing"),
        context={
            "source_room": source_room.name,
            "dest_room": dest_room.name,
            "existing_portals": existing_source_portals,
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_source_portals),
        toolbox=None,
    )
    broadcast_generated(
        message=format_prompt(
            "world_generate_portal_broadcast_outgoing", outgoing_name=outgoing_name
        )
    )

    incoming_name = loop_retry(
        agent,
        get_prompt("world_generate_portal_name_incoming"),
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

    broadcast_generated(
        message=format_prompt(
            "world_generate_portal_broadcast_incoming",
            incoming_name=incoming_name,
            outgoing_name=outgoing_name,
        )
    )

    # TODO: generate descriptions for the portals

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
        get_prompt("world_generate_item_name"),
        context={
            "dest_note": dest_note,
            "existing_items": existing_items,
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_items),
        toolbox=None,
    )

    broadcast_generated(
        message=format_prompt("world_generate_item_broadcast_item", name=name)
    )
    desc = agent(get_prompt("world_generate_item_description"), name=name)

    actions = {}
    item = Item(name=name, description=desc, actions=actions)
    generate_system_attributes(agent, world, item, systems)

    world_config = get_world_config()
    effect_count = resolve_int_range(world_config.size.item_effects) or 0
    broadcast_generated(
        message=format_prompt(
            "world_generate_item_broadcast_effects",
            effect_count=effect_count,
            name=name,
        )
    )

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
        get_prompt("world_generate_character_name"),
        context={
            "additional_prompt": additional_prompt,
            "dest_room": dest_room.name,
            "existing_characters": existing_characters,
            "world_theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_characters),
        toolbox=None,
    )

    broadcast_generated(
        message=format_prompt("world_generate_character_broadcast_name", name=name)
    )
    description = agent(
        get_prompt("world_generate_character_description"),
        additional_prompt=additional_prompt,
        detail_prompt=detail_prompt,
        name=name,
    )
    backstory = agent(
        get_prompt("world_generate_character_backstory"),
        additional_prompt=additional_prompt,
        detail_prompt=detail_prompt,
        name=name,
    )

    character = Character(
        name=name, backstory=backstory, description=description, actions={}, items=[]
    )
    generate_system_attributes(agent, world, character, systems)

    # generate the character's inventory
    world_config = get_world_config()
    item_count = resolve_int_range(world_config.size.character_items) or 0
    broadcast_generated(
        message=format_prompt(
            "world_generate_character_broadcast_items", item_count=item_count, name=name
        )
    )

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
        # TODO: make sure characters have an agent
        logger.info(f"adding character {name} to end of world turn order")
        world.order.append(name)

    return character


def generate_effect(agent: Agent, world: World, entity: Item) -> EffectPattern:
    entity_type = entity.type
    existing_effects = [effect.name for effect in entity.effects]

    name = loop_retry(
        agent,
        get_prompt("world_generate_effect_name"),
        context={
            "entity_name": entity.name,
            "entity_type": entity_type,
            "existing_effects": existing_effects,
            "theme": world.theme,
        },
        result_parser=duplicate_name_parser(existing_effects),
        toolbox=None,
    )
    broadcast_generated(
        message=format_prompt("world_generate_effect_broadcast_effect", name=name)
    )

    description = agent(
        get_prompt("world_generate_effect_description"),
        name=name,
    )

    cooldown = loop_retry(
        agent,
        get_prompt("world_generate_effect_cooldown"),
        context={
            "name": name,
        },
        result_parser=int_result,
        toolbox=None,
    )

    uses = loop_retry(
        agent,
        get_prompt("world_generate_effect_uses"),
        context={
            "name": name,
        },
        result_parser=int_result,
        toolbox=None,
    )

    if uses == -1:
        uses = None

    attribute_names = agent(
        get_prompt("world_generate_effect_attribute_names"),
        name=name,
    )

    attributes = []
    for attribute_name in attribute_names.split(","):
        attribute_name = normalize_name(attribute_name)
        if attribute_name:
            value = agent(
                get_prompt("world_generate_effect_attribute_value"),
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
        get_prompt("world_generate_effect_duration"),
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

        raise ValueError(get_prompt("world_generate_effect_error_application"))

    application = loop_retry(
        agent,
        get_prompt("world_generate_effect_application"),
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
    world_config = get_world_config()

    for room in rooms:
        num_portals = resolve_int_range(world_config.size.portals) or 0

        if len(room.portals) >= num_portals:
            logger.info(f"room {room.name} already has enough portals")
            continue

        broadcast_generated(
            format_prompt(
                "world_generate_room_broadcast_portals",
                num_portals=num_portals,
                name=room.name,
            )
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
    world_config = get_world_config()
    room_count = room_count or resolve_int_range(world_config.size.rooms) or 0

    broadcast_generated(message=format_prompt("world_generate_world_broadcast_theme"))
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
