from json import loads
from typing import Any, Callable, Dict, List, Literal, Union
from uuid import uuid4

from pydantic import Field

from .base import dataclass
from .entity import Actor, Item, Room, WorldEntity


def uuid() -> str:
    return uuid4().hex


class BaseEvent:
    """
    A base event class.
    """

    id: str
    type: str


@dataclass
class GenerateEvent(BaseEvent):
    """
    A new entity has been generated.
    """

    id = Field(default_factory=uuid)
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
class ActionEvent(BaseEvent):
    """
    An actor has taken an action.
    """

    id = Field(default_factory=uuid)
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
class PromptEvent(BaseEvent):
    """
    A prompt for an actor to take an action.
    """

    id = Field(default_factory=uuid)
    type = "prompt"
    prompt: str
    room: Room
    actor: Actor


@dataclass
class ReplyEvent(BaseEvent):
    """
    An actor has replied with text.

    This is the non-JSON version of an ActionEvent.
    """

    id = Field(default_factory=uuid)
    type = "reply"
    text: str
    room: Room
    actor: Actor

    @staticmethod
    def from_text(text: str, room: Room, actor: Actor) -> "ReplyEvent":
        return ReplyEvent(text=text, room=room, actor=actor)


@dataclass
class ResultEvent(BaseEvent):
    """
    A result of an action.
    """

    id = Field(default_factory=uuid)
    type = "result"
    result: str
    room: Room
    actor: Actor


@dataclass
class StatusEvent(BaseEvent):
    """
    A status broadcast event with text.
    """

    id = Field(default_factory=uuid)
    type = "status"
    text: str
    room: Room | None = None
    actor: Actor | None = None


@dataclass
class SnapshotEvent(BaseEvent):
    """
    A snapshot of the world state.

    This one is slightly unusual, because the world has already been dumped to a JSON-compatible dictionary.
    That is especially important for the memory, which is a dictionary of actor names to lists of messages.
    """

    id = Field(default_factory=uuid)
    type = "snapshot"
    world: Dict[str, Any]
    memory: Dict[str, List[Any]]
    step: int


@dataclass
class PlayerEvent(BaseEvent):
    """
    A player joining or leaving the game.
    """

    id = Field(default_factory=uuid)
    type = "player"
    status: Literal["join", "leave"]
    character: str
    client: str


@dataclass
class PlayerListEvent(BaseEvent):
    """
    A list of players in the game and the characters they are playing.
    """

    id = Field(default_factory=uuid)
    type = "players"
    players: Dict[str, str]


@dataclass
class RenderEvent(BaseEvent):
    """
    Images have been rendered.
    """

    id = Field(default_factory=uuid)
    type = "render"
    paths: List[str]
    source: Union["GameEvent", WorldEntity]


# event types
WorldEvent = ActionEvent | PromptEvent | ReplyEvent | ResultEvent | StatusEvent
PlayerEventType = PlayerEvent | PlayerListEvent
GameEvent = GenerateEvent | PlayerEventType | RenderEvent | WorldEvent

# callback types
EventCallback = Callable[[GameEvent], None]
