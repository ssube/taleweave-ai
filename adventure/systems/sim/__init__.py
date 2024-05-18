from .hunger_actions import action_cook, action_eat
from .hygiene_actions import action_wash
from .sleeping_actions import action_sleep

from adventure.logic import load_logic

LOGIC_FILES = [
    "./adventure/sim_systems/environment_logic.yaml",
    "./adventure/sim_systems/hunger_logic.yaml",
    "./adventure/sim_systems/hygiene_logic.yaml",
    "./adventure/sim_systems/mood_logic.yaml",
    "./adventure/sim_systems/sleeping_logic.yaml",
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
