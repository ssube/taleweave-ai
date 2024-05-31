from logging import getLogger
from typing import Dict, List

from taleweave.context import get_current_world, get_prompt_library, subscribe
from taleweave.game_system import FormatPerspective, GameSystem
from taleweave.models.entity import Character, Room, World, WorldEntity
from taleweave.models.event import ActionEvent, GameEvent
from taleweave.utils.search import find_containing_room

logger = getLogger(__name__)


def create_turn_digest(
    active_room: Room, active_character: Character, turn_events: List[GameEvent]
) -> List[str]:
    library = get_prompt_library()
    messages = []
    for event in turn_events:
        if isinstance(event, ActionEvent):
            if event.character == active_character or event.room == active_room:
                prompt_key = f"digest_{event.action}"
                if prompt_key in library.prompts:
                    try:
                        template = library.prompts[prompt_key]
                        message = template.format(event=event)
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

    digest = create_turn_digest(room, entity, buffer)
    return "\n".join(digest)


def initialize_digest(world: World):
    for room in world.rooms:
        for character in room.characters:
            character_buffers[character.name] = []


def init():
    subscribe(GameEvent, digest_listener)
    return [GameSystem("digest", format=format_digest, initialize=initialize_digest)]
