from typing import Dict

from .base import dataclass


@dataclass
class PromptLibrary:
    prompts: Dict[str, str]
