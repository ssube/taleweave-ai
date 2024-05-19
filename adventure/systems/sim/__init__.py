from .hunger_actions import action_cook, action_eat
from .hygiene_actions import action_wash
from .sleeping_actions import action_sleep

from adventure.logic import load_logic

LOGIC_FILES = [
    "./adventure/systems/sim/environment_logic.yaml",
    "./adventure/systems/sim/hunger_logic.yaml",
    "./adventure/systems/sim/hygiene_logic.yaml",
    "./adventure/systems/sim/mood_logic.yaml",
    "./adventure/systems/sim/sleeping_logic.yaml",
]


def init_actions():
    return [
        # hunger
        action_cook,
        action_eat,
        # hygiene
        action_wash,
        # sleeping
        action_sleep,
    ]


def init_logic():
    return [load_logic(filename) for filename in LOGIC_FILES]
