from enum import Enum
from typing import Callable, Protocol

from packit.agent import Agent

from adventure.models.entity import World, WorldEntity


class FormatPerspective(Enum):
    FIRST_PERSON = "first-person"
    SECOND_PERSON = "second-person"
    THIRD_PERSON = "third-person"


# TODO: remove the attributes parameter from all of these
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


class SystemSimulate(Protocol):
    def __call__(self, world: World, step: int) -> None:
        """
        Simulate the world for the given step.
        """
        ...


class GameSystem:
    format: SystemFormat | None = None
    generate: SystemGenerate | None = None
    simulate: SystemSimulate | None = None
    # render: TODO

    def __init__(
        self,
        format: SystemFormat | None = None,
        generate: SystemGenerate | None = None,
        simulate: SystemSimulate | None = None,
    ):
        self.format = format
        self.generate = generate
        self.simulate = simulate

    def __str__(self):
        return f"GameSystem(format={format_callable(self.format)}, generate={format_callable(self.generate)}, simulate={format_callable(self.simulate)})"


def format_callable(fn: Callable | None) -> str:
    if fn:
        return f"{fn.__module__}:{fn.__name__}"

    return "None"
