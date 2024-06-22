from os import path

from taleweave.systems.generic.logic import load_logic

from .crafting.actions import action_craft
from .magic.actions import action_cast
from .movement.actions import action_climb
from .quest.actions import accept_quest, submit_quest
from .writing.actions import action_read, action_write


def logic_path(system: str) -> str:
    return path.join(".", "taleweave", "systems", "rpg", system, "logic.yaml")


SYSTEM_NAMES = [
    "combat",
    "crafting",
    "health",
    "magic",
    "movement",
    "quest",
    "writing",
]


def init_actions():
    return [
        # crafting
        action_craft,
        # magic
        action_cast,
        # movement
        action_climb,
        # quest
        accept_quest,
        submit_quest,
        # writing
        action_read,
        action_write,
    ]


def init_logic():
    systems = []
    for system_name in SYSTEM_NAMES:
        logic_file = logic_path(system_name)
        if path.exists(logic_file):
            systems.append(load_logic(logic_file, name_prefix=system_name))

    return systems
