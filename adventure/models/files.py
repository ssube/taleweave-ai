from typing import List

from .base import dataclass


@dataclass
class WorldPrompt:
    name: str
    theme: str
    flavor: str = ""


@dataclass
class PromptFile:
    prompts: List[WorldPrompt]
