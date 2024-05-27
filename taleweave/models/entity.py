from typing import Callable, Dict, List, Literal

from pydantic import Field

from .base import Attributes, BaseModel, dataclass, uuid
from .effect import EffectPattern, EffectResult
from .planning import Planner

Actions = Dict[str, Callable]


@dataclass
class Item(BaseModel):
    name: str
    description: str
    actions: Actions = Field(default_factory=dict)
    active_effects: List[EffectResult] = Field(default_factory=list)
    attributes: Attributes = Field(default_factory=dict)
    effects: List[EffectPattern] = Field(default_factory=list)
    items: List["Item"] = Field(default_factory=list)
    id: str = Field(default_factory=uuid)
    type: Literal["item"] = "item"


@dataclass
class Character(BaseModel):
    name: str
    backstory: str
    description: str
    planner: Planner = Field(default_factory=Planner)
    actions: Actions = Field(default_factory=dict)
    active_effects: List[EffectResult] = Field(default_factory=list)
    attributes: Attributes = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)
    id: str = Field(default_factory=uuid)
    type: Literal["character"] = "character"


@dataclass
class Portal(BaseModel):
    name: str
    description: str
    destination: str
    actions: Actions = Field(default_factory=dict)
    attributes: Attributes = Field(default_factory=dict)
    id: str = Field(default_factory=uuid)
    type: Literal["portal"] = "portal"


@dataclass
class Room(BaseModel):
    name: str
    description: str
    characters: List[Character] = Field(default_factory=list)
    actions: Actions = Field(default_factory=dict)
    active_effects: List[EffectResult] = Field(default_factory=list)
    attributes: Attributes = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)
    portals: List[Portal] = Field(default_factory=list)
    id: str = Field(default_factory=uuid)
    type: Literal["room"] = "room"


@dataclass
class World(BaseModel):
    name: str
    order: List[str]
    rooms: List[Room]
    theme: str
    id: str = Field(default_factory=uuid)
    type: Literal["world"] = "world"


@dataclass
class WorldState(BaseModel):
    memory: Dict[str, List[str | Dict[str, str]]]
    turn: int
    world: World
    id: str = Field(default_factory=uuid)
    type: Literal["world_state"] = "world_state"


WorldEntity = Room | Character | Item | Portal


@dataclass
class EntityReference:
    character: str | None = None
    item: str | None = None
    portal: str | None = None
    room: str | None = None
