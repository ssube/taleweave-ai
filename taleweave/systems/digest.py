from typing import Dict, List

from taleweave.context import get_current_world, subscribe
from taleweave.game_system import FormatPerspective, GameSystem
from taleweave.models.entity import Character, Room, World, WorldEntity
from taleweave.models.event import ActionEvent, GameEvent
from taleweave.utils.search import find_containing_room


def create_turn_digest(
    active_room: Room, active_character: Character, turn_events: List[GameEvent]
) -> List[str]:
    messages = []
    for event in turn_events:
        if isinstance(event, ActionEvent):
            if event.character == active_character or event.room == active_room:
                if event.action == "move":
                    # TODO: differentiate between entering and leaving
                    messages.append(f"{event.character.name} entered the room.")
                elif event.action == "take":
                    messages.append(
                        f"{event.character.name} picked up the {event.parameters['item']}."
                    )
                elif event.action == "give":
                    messages.append(
                        f"{event.character.name} gave {event.parameters['item']} to {event.parameters['character']}."
                    )
                elif event.action == "ask":
                    messages.append(
                        f"{event.character.name} asked {event.parameters['character']} about something."
                    )
                elif event.action == "tell":
                    messages.append(
                        f"{event.character.name} told {event.parameters['character']} something."
                    )
                elif event.action == "examine":
                    messages.append(
                        f"{event.character.name} examined the {event.parameters['target']}."
                    )

    return messages


character_buffers: Dict[str, List[GameEvent]] = {}


def digest_listener(event: GameEvent):
    if isinstance(event, ActionEvent):
        character = event.character.name

        # append the event to every character's buffer except the one who triggered it
        # the actor should have their buffer reset, because they can only act on their turn

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
