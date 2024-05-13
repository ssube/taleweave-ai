from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass as dataclass  # noqa


class BaseModel:
    type: str
    id: str


def uuid() -> str:
    return uuid4().hex
