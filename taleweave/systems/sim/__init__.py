from os import path

from taleweave.systems.generic.logic import load_logic

from .hunger.actions import action_cook, action_eat
from .hygiene.hygiene_actions import action_wash
from .sleeping.actions import action_sleep


def logic_path(system: str) -> str:
    return path.join(".", "taleweave", "systems", "sim", system, "logic.yaml")


SYSTEM_NAMES = [
    "hunger",
    "hygiene",
    "mood",
    "sleeping",
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
    systems = []
    for system_name in SYSTEM_NAMES:
        logic_file = logic_path(system_name)
        if path.exists(logic_file):
            systems.append(load_logic(logic_file, name_prefix=system_name))

    return systems
