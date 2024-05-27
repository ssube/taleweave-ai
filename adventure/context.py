from contextlib import contextmanager
from logging import getLogger
from types import UnionType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

from packit.agent import Agent
from pyee.base import EventEmitter

from adventure.game_system import GameSystem
from adventure.models.entity import Character, Room, World
from adventure.models.event import GameEvent
from adventure.utils.string import normalize_name

logger = getLogger(__name__)

# world context
current_step = 0
current_world: World | None = None
current_room: Room | None = None
current_character: Character | None = None
dungeon_master: Agent | None = None

# game context
event_emitter = EventEmitter()
game_systems: List[GameSystem] = []
system_data: Dict[str, Any] = {}


# TODO: where should this one go?
character_agents: Dict[str, Tuple[Character, Agent]] = {}

STRING_EVENT_TYPE = "message"


def get_event_name(event: GameEvent | Type[GameEvent]):
    return f"event:{event.type}"


def broadcast(message: str | GameEvent):
    if isinstance(message, GameEvent):
        event_name = get_event_name(message)
        logger.debug(f"broadcasting {event_name}")
        event_emitter.emit(event_name, message)
    else:
        logger.warning("broadcasting a string message is deprecated")
        event_emitter.emit(STRING_EVENT_TYPE, message)


def is_union(type_: Type | UnionType):
    origin = get_origin(type_)
    return origin is UnionType or origin is Union


def subscribe(
    event_type: Type[str] | Type[GameEvent] | UnionType,
    callback: Callable[[GameEvent], None],
):
    if is_union(event_type):
        for t in get_args(event_type):
            subscribe(t, callback)

        return

    if event_type is str:
        event_name = STRING_EVENT_TYPE
    else:
        event_name = get_event_name(event_type)

    logger.debug(f"subscribing {callback.__name__} to {event_type}")
    event_emitter.on(event_name, callback)


def has_dungeon_master():
    return dungeon_master is not None


# region context manager
@contextmanager
def action_context():
    room, character = get_action_context()
    yield room, character


@contextmanager
def world_context():
    world, room, character = get_world_context()
    yield world, room, character


# endregion


# region context getters
def get_action_context() -> Tuple[Room, Character]:
    if not current_room:
        raise ValueError("The current room must be set before calling action functions")
    if not current_character:
        raise ValueError(
            "The current character must be set before calling action functions"
        )

    return (current_room, current_character)


def get_world_context() -> Tuple[World, Room, Character]:
    if not current_world:
        raise ValueError(
            "The current world must be set before calling action functions"
        )
    if not current_room:
        raise ValueError("The current room must be set before calling action functions")
    if not current_character:
        raise ValueError(
            "The current character must be set before calling action functions"
        )

    return (current_world, current_room, current_character)


def get_current_world() -> World | None:
    return current_world


def get_current_room() -> Room | None:
    return current_room


def get_current_character() -> Character | None:
    return current_character


def get_current_step() -> int:
    return current_step


def get_dungeon_master() -> Agent:
    if not dungeon_master:
        raise ValueError(
            "The dungeon master must be set before calling action functions"
        )

    return dungeon_master


def get_game_systems() -> List[GameSystem]:
    return game_systems


def get_system_data(system: str) -> Any | None:
    return system_data.get(system)


# endregion


# region context setters
def set_current_world(world: World | None):
    global current_world
    current_world = world


def set_current_room(room: Room | None):
    global current_room
    current_room = room


def set_current_character(character: Character | None):
    global current_character
    current_character = character


def set_current_step(step: int):
    global current_step
    current_step = step


def set_character_agent(name, character, agent):
    character_agents[name] = (character, agent)


def set_dungeon_master(agent):
    global dungeon_master
    dungeon_master = agent


def set_game_systems(systems: Sequence[GameSystem]):
    global game_systems
    game_systems = list(systems)


def set_system_data(system: str, data: Any):
    system_data[system] = data


# endregion


# region search functions
def get_character_for_agent(agent):
    return next(
        (
            inner_character
            for inner_character, inner_agent in character_agents.values()
            if inner_agent == agent
        ),
        None,
    )


def get_agent_for_character(character):
    return next(
        (
            inner_agent
            for inner_character, inner_agent in character_agents.values()
            if inner_character == character
        ),
        None,
    )


def get_character_agent_for_name(name):
    return next(
        (
            (character, agent)
            for character, agent in character_agents.values()
            if normalize_name(character.name) == normalize_name(name)
        ),
        (None, None),
    )


def get_all_character_agents():
    return list(character_agents.values())


# endregion
