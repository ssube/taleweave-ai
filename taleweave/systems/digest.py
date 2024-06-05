from logging import getLogger
from typing import Any, Dict, List

from taleweave.context import get_current_world, get_prompt_library, subscribe
from taleweave.game_system import FormatPerspective, GameSystem
from taleweave.models.entity import Character, Room, World, WorldEntity
from taleweave.models.event import ActionEvent, GameEvent
from taleweave.utils.prompt import format_str
from taleweave.utils.search import find_containing_room, find_portal, find_room

logger = getLogger(__name__)


def create_move_digest(
    world: World,
    active_room: Room,
    active_character: Character,
    event: ActionEvent,
) -> str:
    source_room = event.room
    direction = str(event.parameters.get("direction"))
    destination_portal = find_portal(world, direction)
    if not destination_portal:
        raise ValueError(f"Could not find portal for direction {direction}")

    destination_room = find_room(world, destination_portal.destination)
    if not destination_room:
        raise ValueError(
            f"Could not find destination room {destination_portal.destination}"
        )

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
        raise ValueError(f"Could not find source portal for {destination_portal.name}")

    mode = "self" if (event.character == active_character) else "other"
    mood = "enter" if (destination_room == active_room) else "exit"

    message = format_str(
        f"digest_move_{mode}_{mood}",
        destination_portal=destination_portal,
        destination_room=destination_room,
        direction=direction,
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
                message = create_move_digest(
                    world, active_room, active_character, event
                )
                messages.append(message)
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
) -> str:
    if not isinstance(entity, Character):
        return ""

    buffer = character_buffers[entity.name]

    world = get_current_world()
    if not world:
        raise ValueError("No world found")

    room = find_containing_room(world, entity)
    if not room:
        raise ValueError("Character not found in any room")

    digest = create_turn_digest(world, room, entity, buffer)
    return "\n".join(digest)


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
            "digest",
            format=format_digest,
            generate=generate_digest,
            initialize=initialize_digest,
        )
    ]
