from os import path

from taleweave.systems.generic.logic import load_logic


def logic_path(system: str) -> str:
    return path.join(".", "taleweave", "systems", "environment", system, "logic.yaml")


SYSTEM_NAMES = [
    "humidity",
    "temperature",
    "weather",
]


def init_logic():
    systems = []
    for system_name in SYSTEM_NAMES:
        logic_file = logic_path(system_name)
        if path.exists(logic_file):
            systems.append(load_logic(logic_file))

    return systems
