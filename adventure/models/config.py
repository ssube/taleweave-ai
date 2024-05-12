from typing import Dict, List

from .base import dataclass


@dataclass
class Range:
    min: int
    max: int


@dataclass
class Size:
    width: int
    height: int


@dataclass
class DiscordBotConfig:
    channels: List[str]
    content_intent: bool = False


@dataclass
class BotConfig:
    discord: DiscordBotConfig


@dataclass
class RenderConfig:
    cfg: Range
    checkpoints: List[str]
    path: str
    sizes: Dict[str, Size]
    steps: Range


@dataclass
class Config:
    bot: BotConfig
    render: RenderConfig
