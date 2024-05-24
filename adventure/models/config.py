from typing import Dict, List

from .base import IntRange, dataclass


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
    cfg: IntRange
    checkpoints: List[str]
    path: str
    sizes: Dict[str, Size]
    steps: IntRange


@dataclass
class WebsocketServerConfig:
    host: str
    port: int


@dataclass
class ServerConfig:
    websocket: WebsocketServerConfig


@dataclass
class WorldSizeConfig:
    actor_items: IntRange
    item_effects: IntRange
    portals: IntRange
    room_actors: IntRange
    room_items: IntRange
    rooms: IntRange


@dataclass
class WorldConfig:
    size: WorldSizeConfig


@dataclass
class Config:
    bot: BotConfig
    render: RenderConfig
    server: ServerConfig
    world: WorldConfig


DEFAULT_CONFIG = Config(
    bot=BotConfig(discord=DiscordBotConfig(channels=["adventure"])),
    render=RenderConfig(
        cfg=IntRange(min=5, max=8),
        checkpoints=[
            "diffusion-sdxl-dynavision-0-5-5-7.safetensors",
        ],
        path="/tmp/adventure-images",
        sizes={
            "landscape": Size(width=1024, height=768),
            "portrait": Size(width=768, height=1024),
            "square": Size(width=768, height=768),
        },
        steps=IntRange(min=30, max=30),
    ),
    server=ServerConfig(websocket=WebsocketServerConfig(host="localhost", port=8001)),
    world=WorldConfig(
        size=WorldSizeConfig(
            actor_items=IntRange(min=0, max=2),
            item_effects=IntRange(min=1, max=2),
            portals=IntRange(min=1, max=3),
            rooms=IntRange(min=3, max=6),
            room_actors=IntRange(min=1, max=3),
            room_items=IntRange(min=1, max=3),
        )
    ),
)
