from json import loads
from typing import Any, Callable, Dict, List, Literal

from .base import dataclass
from .entity import Actor, Item, Room, WorldEntity


@dataclass
class BaseEvent:
    """
    A base event class.
    """

    type: str


@dataclass
class GenerateEvent:
    """
    A new entity has been generated.
    """

    type = "generate"
    name: str
    entity: WorldEntity | None = None

    @staticmethod
    def from_name(name: str) -> "GenerateEvent":
        return GenerateEvent(name=name)

    @staticmethod
    def from_entity(entity: WorldEntity) -> "GenerateEvent":
        return GenerateEvent(name=entity.name, entity=entity)


@dataclass
class ActionEvent:
    """
    An actor has taken an action.
    """

    type = "action"
    action: str
    parameters: Dict[str, bool | float | int | str]

    room: Room
    actor: Actor
    item: Item | None = None

    @staticmethod
    def from_json(json: str, room: Room, actor: Actor) -> "ActionEvent":
        openai_json = loads(json)
        return ActionEvent(
            action=openai_json["function"],
            parameters=openai_json["parameters"],
            room=room,
            actor=actor,
            item=None,
        )


@dataclass
class PromptEvent:
    """
    A prompt for an actor to take an action.
    """

    type = "prompt"
    prompt: str
    room: Room
    actor: Actor

    @staticmethod
    def from_text(prompt: str, room: Room, actor: Actor) -> "PromptEvent":
        return PromptEvent(prompt=prompt, room=room, actor=actor)


@dataclass
class ReplyEvent:
    """
    An actor has replied with text.

    This is the non-JSON version of an ActionEvent.
    """

    type = "reply"
    text: str
    room: Room
    actor: Actor

    @staticmethod
    def from_text(text: str, room: Room, actor: Actor) -> "ReplyEvent":
        return ReplyEvent(text=text, room=room, actor=actor)


@dataclass
class ResultEvent:
    """
    A result of an action.
    """

    type = "result"
    result: str
    room: Room
    actor: Actor


@dataclass
class StatusEvent:
    """
    A status broadcast event with text.
    """

    type = "status"
    text: str
    room: Room | None = None
    actor: Actor | None = None


@dataclass
class SnapshotEvent:
    """
    A snapshot of the world state.

    This one is slightly unusual, because the world has already been dumped to a JSON-compatible dictionary.
    That is especially important for the memory, which is a dictionary of actor names to lists of messages.
    """

    type = "snapshot"
    world: Dict[str, Any]
    memory: Dict[str, List[Any]]
    step: int


@dataclass
class PlayerEvent:
    """
    A player joining or leaving the game.
    """

    type = "player"
    status: Literal["join", "leave"]
    character: str
    client: str


# event types
WorldEvent = ActionEvent | PromptEvent | ReplyEvent | ResultEvent | StatusEvent
GameEvent = GenerateEvent | PlayerEvent | WorldEvent

# callback types
EventCallback = Callable[[GameEvent], None]
