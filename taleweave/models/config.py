from typing import Dict, List

from .base import Attributes, IntRange, dataclass


@dataclass
class Size:
    width: int
    height: int


@dataclass
class DiscordBotConfig:
    channels: List[str]
    command_prefix: str
    name_command: str
    name_title: str
    content_intent: bool = False


@dataclass
class BotConfig:
    discord: DiscordBotConfig


@dataclass
class RenderConfig:
    cfg: int | IntRange
    checkpoints: List[str]
    count: int
    path: str
    sizes: Dict[str, Size]
    steps: int | IntRange


@dataclass
class WebsocketServerConfig:
    host: str
    port: int


@dataclass
class ServerConfig:
    websocket: WebsocketServerConfig


@dataclass
class SystemsConfig:
    """
    Configuration for the game systems.
    """

    data: Attributes


@dataclass
class WorldCharacterConfig:
    conversation_limit: int
    event_limit: int
    note_limit: int


@dataclass
class WorldSizeConfig:
    character_items: int | IntRange
    item_effects: int | IntRange
    portals: int | IntRange
    room_characters: int | IntRange
    room_items: int | IntRange
    rooms: int | IntRange


@dataclass
class WorldTurnConfig:
    action_retries: int
    planning_steps: int
    planning_retries: int


@dataclass
class WorldConfig:
    character: WorldCharacterConfig
    size: WorldSizeConfig
    turn: WorldTurnConfig


@dataclass
class Config:
    bot: BotConfig
    render: RenderConfig
    server: ServerConfig
    systems: SystemsConfig
    world: WorldConfig


DEFAULT_CONFIG = Config(
    bot=BotConfig(
        discord=DiscordBotConfig(
            channels=["taleweave"],
            command_prefix="!",
            name_command="taleweave",
            name_title="Taleweave AI",
        ),
    ),
    render=RenderConfig(
        cfg=IntRange(min=5, max=8),
        checkpoints=[
            "diffusion-sdxl-dynavision-0-5-5-7.safetensors",
        ],
        count=2,
        path="/tmp/taleweave-images",
        sizes={
            "landscape": Size(width=1024, height=768),
            "portrait": Size(width=768, height=1024),
            "square": Size(width=768, height=768),
        },
        steps=30,
    ),
    server=ServerConfig(websocket=WebsocketServerConfig(host="localhost", port=8001)),
    systems=SystemsConfig(data={}),
    world=WorldConfig(
        character=WorldCharacterConfig(
            conversation_limit=2,
            event_limit=5,
            note_limit=10,
        ),
        size=WorldSizeConfig(
            character_items=IntRange(min=0, max=2),
            item_effects=IntRange(min=1, max=1),
            portals=IntRange(min=1, max=3),
            rooms=IntRange(min=3, max=6),
            room_characters=IntRange(min=1, max=3),
            room_items=IntRange(min=1, max=3),
        ),
        turn=WorldTurnConfig(
            action_retries=5,
            planning_steps=3,
            planning_retries=3,
        ),
    ),
)
