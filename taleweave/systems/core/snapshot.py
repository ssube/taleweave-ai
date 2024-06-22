from logging import getLogger
from typing import Any

from taleweave.game_system import GameSystem
from taleweave.models.entity import World
from taleweave.state import save_world_state

logger = getLogger(__name__)


def simulate_snapshot(world: World, turn: int, data: Any | None = None):
    logger.info("taking snapshot of world state")
    world_state_file = "TODO"  # TODO: get world state file from somewhere
    save_world_state(world, turn, world_state_file)


def init():
    return [GameSystem("snapshot", simulate=simulate_snapshot)]
