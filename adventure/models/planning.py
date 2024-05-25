from typing import List

from pydantic import Field

from adventure.models.base import dataclass


@dataclass
class CalendarEvent:
    name: str
    turn: int


@dataclass
class Calendar:
    events: List[CalendarEvent] = Field(default_factory=list)


@dataclass
class Planner:
    calendar: Calendar = Field(default_factory=Calendar)
    notes: List[str] = Field(default_factory=list)
