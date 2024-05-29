from functools import partial
from typing import List
from taleweave.context import get_dungeon_master
from taleweave.models.base import dataclass
from taleweave.models.entity import World
from taleweave.systems.logic import load_logic
from taleweave.game_system import GameSystem
from packit.agent import Agent
from taleweave.models.entity import Room, WorldEntity
from taleweave.utils.string import or_list
from packit.results import enum_result
from packit.loops import loop_retry
from logging import getLogger

logger = getLogger(__name__)


LOGIC_FILES = [
    "./taleweave/systems/weather/weather_logic.yaml",
]


@dataclass
class TimeOfDay:
    name: str
    start: int
    end: int


GAME_START_HOUR = 8
TURNS_PER_DAY = 24

TIMES_OF_DAY: List[TimeOfDay] = [
    TimeOfDay("night", 0, 4),
    TimeOfDay("morning", 5, 7),
    TimeOfDay("day", 8, 18),
    TimeOfDay("evening", 20, 22),
    TimeOfDay("night", 23, 24),
]


def get_time_of_day(turn: int) -> TimeOfDay:
    hour = (turn + GAME_START_HOUR) % TURNS_PER_DAY
    for time in TIMES_OF_DAY:
        if time.start <= hour <= time.end:
            return time
    return TIMES_OF_DAY[0]


def initialize_weather(world: World):
    time_of_day = get_time_of_day(0)
    for room in world.rooms:
        logger.info(f"initializing weather for {room.name}")
        room.attributes["time"] = time_of_day.name

        if "environment" not in room.attributes:
            dungeon_master = get_dungeon_master()
            generate_room_weather(dungeon_master, world.theme, room)


def generate_room_weather(agent: Agent, theme: str, entity: Room) -> None:
    environment_options = ["indoor", "outdoor"]
    environment_result = partial(enum_result, enum=environment_options)
    environment = loop_retry(
        agent,
        "Is this room indoors or outdoors?"
        "Reply with a single word: {environment_list}.\n\n"
        "{description}",
        context={
            "environment_list": or_list(environment_options),
            "description": entity.description,
        },
        result_parser=environment_result,
    )
    entity.attributes["environment"] = environment
    logger.info(f"generated environment for {entity.name}: {environment}")


def generate_weather(agent: Agent, theme: str, entity: WorldEntity) -> None:
    if isinstance(entity, Room):
        if "environment" not in entity.attributes:
            generate_room_weather(agent, theme, entity)


def simulate_weather(world: World, turn: int, data: None = None):
    time_of_day = get_time_of_day(turn)
    for room in world.rooms:
        room.attributes["time"] = time_of_day.name


def init():
    logic_systems = [load_logic(filename) for filename in LOGIC_FILES]
    return [
        *logic_systems,
        GameSystem(
            "weather",
            generate=generate_weather,
            initialize=initialize_weather,
            simulate=simulate_weather,
        ),
    ]
