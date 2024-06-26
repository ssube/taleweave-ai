from logging import getLogger
from typing import Any, Dict, List

from taleweave.context import get_current_world, get_prompt_library, subscribe
from taleweave.game_system import FormatPerspective, GameSystem
from taleweave.models.entity import Character, Room, World, WorldEntity
from taleweave.models.event import ActionEvent, GameEvent
from taleweave.utils.search import find_containing_room, find_portal, find_room
from taleweave.utils.template import format_prompt, format_str

logger = getLogger(__name__)


def create_move_digest(
    world: World,
    active_room: Room,
    active_character: Character,
    event: ActionEvent,
) -> str | None:
    source_room = event.room
    direction = str(event.parameters.get("direction"))
    destination_portal = find_portal(world, direction)
    if not destination_portal:
        logger.warning(f"Could not find portal for direction {direction}")
        return None

    destination_room = find_room(world, destination_portal.destination)
    if not destination_room:
        logger.warning(
            f"Could not find destination room {destination_portal.destination}"
        )
        return None

    if not (destination_room == source_room or destination_room == active_room):
        return None

    # look up the source portal
    source_portal = next(
        (
            portal
            for portal in destination_room.portals
            if portal.destination == source_room.name
        ),
        None,
    )
    if not source_portal:
        logger.warning(f"Could not find source portal for {destination_portal.name}")
        return None

    character_mode = "self" if (event.character == active_character) else "other"
    direction_mode = "enter" if (destination_room == active_room) else "exit"

    message = format_prompt(
        f"digest_move_{character_mode}_{direction_mode}",
        destination_portal=destination_portal,
        destination_room=destination_room,
        direction=direction,
        event=event,
        source_portal=source_portal,
        source_room=source_room,
    )
    return message


def create_turn_digest(
    world: World,
    active_room: Room,
    active_character: Character,
    turn_events: List[GameEvent],
) -> List[str]:
    library = get_prompt_library()
    messages = []
    for event in turn_events:
        if isinstance(event, ActionEvent):
            # special handling for move actions
            if event.action == "action_move":
                try:
                    message = create_move_digest(
                        world, active_room, active_character, event
                    )
                    if message:
                        messages.append(message)
                except Exception:
                    logger.exception(
                        "error formatting digest for move event: %s", event
                    )
            elif event.character == active_character or event.room == active_room:
                prompt_key = f"digest_{event.action}"
                if prompt_key in library.prompts:
                    try:
                        template = library.prompts[prompt_key]
                        message = format_str(
                            template,
                            active_character=active_character,
                            active_room=active_room,
                            event=event,
                        )
                        messages.append(message)
                    except Exception:
                        logger.exception("error formatting digest event: %s", event)

    return messages


character_buffers: Dict[str, List[GameEvent]] = {}


def digest_listener(event: GameEvent):
    if isinstance(event, ActionEvent):
        character = event.character.name

        # append the event to every character's buffer except the one who triggered it. the
        # acting character should have their buffer reset, because they can only act on their turn

        for name, buffer in character_buffers.items():
            if name == character:
                buffer.clear()
            else:
                buffer.append(event)


def format_digest(
    entity: WorldEntity,
    perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
) -> List[str]:
    if not isinstance(entity, Character):
        return []

    if perspective != FormatPerspective.SECOND_PERSON:
        return []

    buffer = character_buffers[entity.name]

    world = get_current_world()
    if not world:
        raise ValueError("No world found")

    room = find_containing_room(world, entity)
    if not room:
        raise ValueError("Character not found in any room")

    digest = create_turn_digest(world, room, entity, buffer)
    return digest


def generate_digest(agent: Any, world: World, entity: WorldEntity):
    if isinstance(entity, Character):
        if entity.name not in character_buffers:
            character_buffers[entity.name] = []


def initialize_digest(world: World):
    for room in world.rooms:
        for character in room.characters:
            character_buffers[character.name] = []


def init():
    subscribe(GameEvent, digest_listener)
    return [
        GameSystem(
            "summary",
            format=format_digest,
            generate=generate_digest,
            initialize=initialize_digest,
        )
    ]
