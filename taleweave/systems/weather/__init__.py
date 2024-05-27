from typing import List
from taleweave.models.base import dataclass
from taleweave.models.entity import World
from taleweave.systems.logic import load_logic
from taleweave.game_system import GameSystem

LOGIC_FILES = [
    "./taleweave/systems/weather/weather_logic.yaml",
]


@dataclass
class TimeOfDay:
    name: str
    start: int
    end: int


TURNS_PER_DAY = 24

TIMES_OF_DAY: List[TimeOfDay] = [
    TimeOfDay("night", 0, 4),
    TimeOfDay("morning", 5, 7),
    TimeOfDay("day", 8, 18),
    TimeOfDay("evening", 20, 22),
    TimeOfDay("night", 23, 24),
]


def get_time_of_day(turn: int) -> TimeOfDay:
    hour = turn % TURNS_PER_DAY
    for time in TIMES_OF_DAY:
        if time.start <= hour <= time.end:
            return time
    return TIMES_OF_DAY[0]


def simulate_weather(world: World, turn: int, data: None = None):
    time_of_day = get_time_of_day(turn)
    for room in world.rooms:
        room.attributes["time"] = time_of_day.name


def init_systems():
    return [GameSystem("weather", simulate=simulate_weather)]


def init_logic():
    return [load_logic(filename) for filename in LOGIC_FILES]
