from typing import TYPE_CHECKING, Callable, Dict, List

from pydantic import Field

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass as dataclass  # noqa


Actions = Dict[str, Callable]


@dataclass
class Item:
    name: str
    description: str
    actions: Actions = Field(default_factory=dict)
    attributes: Dict[str, str] = Field(default_factory=dict)


@dataclass
class Actor:
    name: str
    backstory: str
    description: str
    actions: Actions = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)
    attributes: Dict[str, str] = Field(default_factory=dict)


@dataclass
class Room:
    name: str
    description: str
    portals: Dict[str, str] = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)
    actors: List[Actor] = Field(default_factory=list)
    actions: Actions = Field(default_factory=dict)
    attributes: Dict[str, str] = Field(default_factory=dict)


@dataclass
class World:
    name: str
    order: List[str]
    rooms: List[Room]
    theme: str


@dataclass
class WorldState:
    memory: Dict[str, List[str | Dict[str, str]]]
    step: int
    world: World
