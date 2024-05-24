from typing import List, Literal

from pydantic import Field

from .base import FloatRange, IntRange, dataclass, uuid


@dataclass
class StringEffectPattern:
    name: str
    append: str | List[str] | None = None
    prepend: str | List[str] | None = None
    set: str | List[str] | None = None


@dataclass
class FloatEffectPattern:
    name: str
    set: float | FloatRange | None = None
    offset: float | FloatRange | None = None
    multiply: float | FloatRange | None = None


@dataclass
class IntEffectPattern:
    name: str
    set: int | IntRange | None = None
    offset: int | IntRange | None = None
    multiply: float | FloatRange | None = None


@dataclass
class BooleanEffectPattern:
    name: str
    set: bool | None = None
    toggle: bool | None = None


AttributeEffectPattern = (
    StringEffectPattern | FloatEffectPattern | IntEffectPattern | BooleanEffectPattern
)


@dataclass
class EffectPattern:
    """
    TODO: should this be an EffectTemplate?
    """

    name: str
    description: str
    application: Literal["permanent", "temporary"]
    duration: int | IntRange | None = None
    attributes: List[AttributeEffectPattern] = Field(default_factory=list)
    id: str = Field(default_factory=uuid)
    type: Literal["effect_pattern"] = "effect_pattern"


@dataclass
class BooleanEffectResult:
    name: str
    set: bool | None = None
    toggle: bool | None = None


@dataclass
class FloatEffectResult:
    name: str
    set: float | None = None
    offset: float | None = None
    multiply: float | None = None


@dataclass
class IntEffectResult:
    name: str
    set: int | None = None
    offset: int | None = None
    multiply: float | None = None  # still needs to be a float for decimals/division


@dataclass
class StringEffectResult:
    name: str
    append: str | None = None
    prepend: str | None = None
    set: str | None = None


AttributeEffectResult = (
    BooleanEffectResult | FloatEffectResult | IntEffectResult | StringEffectResult
)


@dataclass
class EffectResult:
    name: str
    description: str
    duration: int | None = None
    attributes: List[AttributeEffectResult] = Field(default_factory=list)
    id: str = Field(default_factory=uuid)
    type: Literal["effect_result"] = "effect_result"
