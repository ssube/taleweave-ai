from .crafting_actions import action_craft
from .language_actions import action_read
from .magic_actions import action_cast
from .movement_actions import action_climb


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
    return []
