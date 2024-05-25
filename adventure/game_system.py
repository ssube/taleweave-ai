from enum import Enum
from typing import Any, Callable, Protocol

from packit.agent import Agent

from adventure.models.entity import World, WorldEntity


class FormatPerspective(Enum):
    FIRST_PERSON = "first-person"
    SECOND_PERSON = "second-person"
    THIRD_PERSON = "third-person"


class SystemFormat(Protocol):
    def __call__(
        self,
        entity: WorldEntity,
        perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
    ) -> str:
        # TODO: should this return a list?
        ...


class SystemGenerate(Protocol):
    def __call__(self, agent: Agent, theme: str, entity: WorldEntity) -> None:
        """
        Generate a new world entity based on the given theme and entity.
        """
        ...


class SystemInitialize(Protocol):
    def __call__(self, world: World) -> Any:
        """
        Initialize the system for the given world.
        """
        ...


class SystemSimulate(Protocol):
    def __call__(self, world: World, step: int, data: Any | None = None) -> None:
        """
        Simulate the world for the given step.
        """
        ...


class SystemData:
    load: Callable[[str], Any]
    save: Callable[[str, Any], None]

    def __init__(self, load: Callable[[str], Any], save: Callable[[str, Any], None]):
        self.load = load
        self.save = save


class GameSystem:
    name: str
    data: SystemData | None = None
    format: SystemFormat | None = None
    generate: SystemGenerate | None = None
    initialize: SystemInitialize | None = None
    simulate: SystemSimulate | None = None
    # render: TODO

    def __init__(
        self,
        name: str,
        *,
        data: SystemData | None = None,
        format: SystemFormat | None = None,
        generate: SystemGenerate | None = None,
        initialize: SystemInitialize | None = None,
        simulate: SystemSimulate | None = None,
    ):
        self.name = name
        self.data = data
        self.format = format
        self.generate = generate
        self.initialize = initialize
        self.simulate = simulate

    def __str__(self):
        return f"GameSystem({self.name})"

    def __repr__(self):
        return str(self)
