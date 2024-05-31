from typing import List

from .base import dataclass


@dataclass
class WorldPrompt:
    name: str
    theme: str
    flavor: str = ""


# TODO: rename to WorldTemplates
@dataclass
class PromptFile:
    prompts: List[WorldPrompt]
