from json import loads
from typing import Any, Callable, Dict, List, Literal, Union

from pydantic import Field

from .base import BaseModel, dataclass, uuid
from .entity import Character, Item, Room, WorldEntity


@dataclass
class GenerateEvent(BaseModel):
    """
    A new entity has been generated.
    """

    name: str
    entity: WorldEntity | None = None
    id: str = Field(default_factory=uuid)
    type: Literal["generate"] = "generate"

    @staticmethod
    def from_name(name: str) -> "GenerateEvent":
        return GenerateEvent(name=name)

    @staticmethod
    def from_entity(entity: WorldEntity) -> "GenerateEvent":
        return GenerateEvent(name=entity.name, entity=entity)


@dataclass
class ActionEvent(BaseModel):
    """
    A character has taken an action.
    """

    action: str
    parameters: Dict[str, bool | float | int | str]

    room: Room
    character: Character
    item: Item | None = None
    id: str = Field(default_factory=uuid)
    type: Literal["action"] = "action"

    @staticmethod
    def from_json(json: str, room: Room, character: Character) -> "ActionEvent":
        openai_json = loads(json)
        return ActionEvent(
            action=openai_json["function"],
            parameters=openai_json["parameters"],
            room=room,
            character=character,
            item=None,
        )


@dataclass
class PromptEvent(BaseModel):
    """
    A prompt for a character to take an action.
    """

    prompt: str
    room: Room
    character: Character
    id: str = Field(default_factory=uuid)
    type: Literal["prompt"] = "prompt"


@dataclass
class ReplyEvent(BaseModel):
    """
    A character has replied with text.

    This is the non-JSON version of an ActionEvent.

    TODO: add the character being replied to.
    """

    text: str
    room: Room
    character: Character
    id: str = Field(default_factory=uuid)
    type: Literal["reply"] = "reply"

    @staticmethod
    def from_text(text: str, room: Room, character: Character) -> "ReplyEvent":
        return ReplyEvent(text=text, room=room, character=character)


@dataclass
class ResultEvent(BaseModel):
    """
    A result of an action.
    """

    result: str
    room: Room
    character: Character
    id: str = Field(default_factory=uuid)
    type: Literal["result"] = "result"


@dataclass
class StatusEvent(BaseModel):
    """
    A status broadcast event with text.
    """

    text: str
    room: Room | None = None
    character: Character | None = None
    id: str = Field(default_factory=uuid)
    type: Literal["status"] = "status"


@dataclass
class SnapshotEvent(BaseModel):
    """
    A snapshot of the world state.

    This one is slightly unusual, because the world has already been dumped to a JSON-compatible dictionary.
    That is especially important for the memory, which is a dictionary of character names to lists of messages.
    """

    world: Dict[str, Any]
    memory: Dict[str, List[Any]]
    step: int
    id: str = Field(default_factory=uuid)
    type: Literal["snapshot"] = "snapshot"


@dataclass
class PlayerEvent(BaseModel):
    """
    A player joining or leaving the game.
    """

    status: Literal["join", "leave"]
    character: str
    client: str
    id: str = Field(default_factory=uuid)
    type: Literal["player"] = "player"


@dataclass
class PlayerListEvent(BaseModel):
    """
    A list of players in the game and the characters they are playing.
    """

    players: Dict[str, str]
    id: str = Field(default_factory=uuid)
    type: Literal["players"] = "players"


@dataclass
class RenderEvent(BaseModel):
    """
    Images have been rendered.
    """

    paths: List[str]
    prompt: str
    source: Union["GameEvent", WorldEntity]
    title: str
    id: str = Field(default_factory=uuid)
    type: Literal["render"] = "render"


# event types
WorldEvent = ActionEvent | PromptEvent | ReplyEvent | ResultEvent | StatusEvent
PlayerEventType = PlayerEvent | PlayerListEvent
GameEvent = GenerateEvent | PlayerEventType | RenderEvent | WorldEvent

# callback types
EventCallback = Callable[[GameEvent], None]
