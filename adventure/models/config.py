from typing import Dict, List

from .base import dataclass


@dataclass
class Range:
    min: int
    max: int
    interval: int = 1


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


DEFAULT_CONFIG = Config(
    bot=BotConfig(discord=DiscordBotConfig(channels=["adventure"])),
    render=RenderConfig(
        cfg=Range(min=5, max=8),
        checkpoints=[
            "diffusion-sdxl-dynavision-0-5-5-7.safetensors",
        ],
        path="/tmp/adventure-images",
        sizes={
            "landscape": Size(width=1024, height=768),
            "portrait": Size(width=768, height=1024),
            "square": Size(width=768, height=768),
        },
        steps=Range(min=30, max=30),
    ),
)
