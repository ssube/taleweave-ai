from .crafting_actions import action_craft
from .language_actions import action_read
from .magic_actions import action_cast
from .movement_actions import action_climb

from taleweave.systems.logic import load_logic

LOGIC_FILES = [
    "./adventure/systems/rpg/weather_logic.yaml",
]


def init_actions():
    return [
        # crafting
        action_craft,
        # language
        action_read,
        # magic
        action_cast,
        # movement
        action_climb,
    ]


def init_logic():
    return [load_logic(filename) for filename in LOGIC_FILES]
