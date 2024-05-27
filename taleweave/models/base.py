from typing import TYPE_CHECKING, Dict
from uuid import uuid4

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass as dataclass  # noqa


AttributeValue = bool | float | int | str
Attributes = Dict[str, AttributeValue]


class BaseModel:
    type: str
    id: str


def uuid() -> str:
    return uuid4().hex


@dataclass
class FloatRange:
    min: float
    max: float
    interval: float = 1.0


@dataclass
class IntRange:
    min: int
    max: int
    interval: int = 1
