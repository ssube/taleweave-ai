import asyncio
from base64 import b64encode
from collections import deque
from io import BytesIO
from json import dumps, loads
from logging import getLogger
from threading import Thread
from typing import Any, Dict, Literal, MutableSequence
from uuid import uuid4

import websockets
from PIL import Image
from pydantic import RootModel

from taleweave.context import (
    broadcast,
    get_character_agent_for_name,
    get_current_world,
    get_game_config,
    set_character_agent,
    subscribe,
)
from taleweave.models.config import WebsocketServerConfig
from taleweave.models.entity import World, WorldEntity
from taleweave.models.event import (
    GameEvent,
    PlayerEvent,
    PlayerListEvent,
    PromptEvent,
    RenderEvent,
)
from taleweave.player import (
    RemotePlayer,
    get_player,
    has_player,
    list_players,
    remove_player,
    set_player,
)
from taleweave.render.comfy import render_entity, render_event
from taleweave.state import snapshot_world, world_json
from taleweave.utils.search import find_character, find_item, find_portal, find_room

logger = getLogger(__name__)

connected = set()
last_snapshot: str | None = None
player_names: Dict[str, str] = {}
recent_events: MutableSequence[GameEvent] = deque(maxlen=100)
recent_json: MutableSequence[str] = deque(maxlen=100)


def get_player_name(client_id: str) -> str:
    return player_names.get(client_id, client_id)


async def handler(websocket):
    id = uuid4().hex
    logger.info("client connected, given id: %s", id)
    connected.add(websocket)

    async def next_turn(event: PromptEvent) -> None:
        await websocket.send(
            dumps(
                {
                    "id": event.id,
                    "type": event.type,
                    "client": id,  # TODO: should this be a field in the PromptEvent?
                    "character": event.character,
                    "prompt": event.prompt,
                    "actions": event.actions,
                },
                default=server_json,
            ),
        )

    def sync_turn(event: PromptEvent) -> bool:
        # TODO: nothing about this is good
        player = get_player(id)
        if player and player.name == event.character.name:
            asyncio.run(next_turn(event))
            return True

        return False

    try:
        await websocket.send(dumps({"type": "id", "client": id}))

        # only send the snapshot once
        if last_snapshot and last_snapshot not in recent_json:
            await websocket.send(last_snapshot)

        for message in recent_json:
            await websocket.send(message)
    except Exception:
        logger.exception("failed to send recent messages to new client")

    while True:
        try:
            # if this socket is attached to a character and that character's turn is active, wait for input
            message = await websocket.recv()
            player_name = get_player_name(id)
            logger.info(f"received message for {player_name}: {message}")

            try:
                data = loads(message)
                message_type = data.get("type", None)
                if message_type == "player":
                    if "name" in data:
                        new_player_name = data["name"]
                        existing_id = next(
                            (
                                k
                                for k, v in player_names.items()
                                if v == new_player_name
                            ),
                            None,
                        )
                        if existing_id is not None:
                            logger.error(
                                f"name {new_player_name} is already in use by {existing_id}"
                            )
                            continue

                        logger.info(
                            f"changing player name for {id} to {new_player_name}"
                        )
                        player_names[id] = new_player_name

                    elif "become" in data:
                        character_name = data["become"]
                        if character_name is not None and has_player(character_name):
                            logger.error(
                                f"character {character_name} is already in use"
                            )
                            continue

                        player = get_player(id)
                        if player and isinstance(player, RemotePlayer):
                            remove_player(id)

                            # TODO: deduplicate this leaving block
                            if character_name is None:
                                player_name = get_player_name(id)
                                logger.info(
                                    "disconnecting player %s from %s",
                                    player_name,
                                    player.name,
                                )
                                broadcast_player_event(
                                    player.name, player_name, "leave"
                                )
                                broadcast_player_list()

                                character, _ = get_character_agent_for_name(player.name)
                                if character and player.fallback_agent:
                                    logger.info(
                                        "restoring LLM agent for %s", player.name
                                    )
                                    set_character_agent(
                                        player.name, character, player.fallback_agent
                                    )

                                continue

                        character, llm_agent = get_character_agent_for_name(
                            character_name
                        )
                        if not character:
                            logger.error(f"Failed to find character {character_name}")
                            continue

                        # prevent any recursive fallback bugs
                        if isinstance(llm_agent, RemotePlayer):
                            logger.warning(
                                "patching recursive fallback for %s", character_name
                            )
                            llm_agent = llm_agent.fallback_agent

                        player = RemotePlayer(
                            character.name,
                            character.backstory,
                            sync_turn,
                            fallback_agent=llm_agent,
                        )
                        set_player(id, player)
                        logger.info(
                            f"client {player_name} is now character {character_name}"
                        )

                        # swap out the LLM agent
                        set_character_agent(character.name, character, player)

                        # notify all clients that this character is now active
                        broadcast_player_event(character_name, player_name, "join")
                        broadcast_player_list()
                elif message_type == "input":
                    player = get_player(id)
                    if player and isinstance(player, RemotePlayer):
                        logger.info(
                            "queueing input for player %s: %s", player.name, data
                        )
                        player.input_queue.put(data["input"])
                elif message_type == "render":
                    render_input(data)

            except Exception:
                logger.exception("failed to parse message")
        except websockets.ConnectionClosedOK:
            break

    connected.remove(websocket)
    if id in player_names:
        del player_names[id]

    # swap out the character for the original agent when they disconnect
    player = get_player(id)
    if player and isinstance(player, RemotePlayer):
        remove_player(id)

        player_name = get_player_name(id)
        logger.info("disconnecting player %s from %s", player_name, player.name)
        broadcast_player_event(player.name, player_name, "leave")
        broadcast_player_list()

        character, _ = get_character_agent_for_name(player.name)
        if character and player.fallback_agent:
            logger.info("restoring LLM agent for %s", player.name)
            set_character_agent(player.name, character, player.fallback_agent)

    logger.info("client disconnected: %s", id)


def find_recent_event(event_id: str) -> GameEvent | None:
    return next((e for e in recent_events if e.id == event_id), None)


def render_input(data):
    world = get_current_world()
    if not world:
        logger.error("no world available")
        return

    if "event" in data:
        event_id = data["event"]
        event = find_recent_event(event_id)
        if event:
            render_event(event)
        else:
            logger.error(f"failed to find event {event_id}")
    elif "character" in data:
        character_name = data["character"]
        character = find_character(world, character_name)
        if character:
            render_entity(character)
        else:
            logger.error(f"failed to find character {character_name}")
    elif "item" in data:
        item_name = data["item"]
        item = find_item(
            world,
            item_name,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if item:
            render_entity(item)
        else:
            logger.error(f"failed to find item {item_name}")
    elif "portal" in data:
        portal_name = data["portal"]
        portal = find_portal(world, portal_name)
        if portal:
            render_entity(portal)
        else:
            logger.error(f"failed to find portal {portal_name}")
    elif "room" in data:
        room_name = data["room"]
        room = find_room(world, room_name)
        if room:
            render_entity(room)
        else:
            logger.error(f"failed to find room {room_name}")
    else:
        logger.error(f"failed to find entity in {data}")


socket_thread = None


def server_json(obj):
    if isinstance(obj, WorldEntity):
        return {
            "id": obj.id,
            "name": obj.name,
            "type": obj.type,
        }

    return world_json(obj)


def send_and_append(id: str, message: Dict):
    json_message = dumps(message, default=server_json)
    recent_json.append(json_message)
    websockets.broadcast(connected, json_message)
    return json_message


def launch_server(config: WebsocketServerConfig):
    global socket_thread

    def run_sockets():
        asyncio.run(server_main())

    logger.info("launching websocket server")
    socket_thread = Thread(target=run_sockets, daemon=True)
    socket_thread.start()

    subscribe(GameEvent, server_event)

    return [socket_thread]


async def server_main():
    config = get_game_config()

    async with websockets.serve(
        handler, config.server.websocket.host, config.server.websocket.port
    ):
        logger.info("websocket server started")
        await asyncio.Future()  # run forever


def server_system(world: World, turn: int, data: Any | None = None):
    global last_snapshot
    id = uuid4().hex  # TODO: should a server be allowed to generate event IDs?
    json_state = {
        **snapshot_world(world, turn),
        "id": id,
        "type": "snapshot",
    }
    last_snapshot = send_and_append(id, json_state)


def server_event(event: GameEvent):
    json_event: Dict[str, Any] = RootModel[event.__class__](event).model_dump()
    json_event.update(
        {
            "id": event.id,
            "type": event.type,
        }
    )

    if isinstance(event, RenderEvent):
        # load and encode the images
        image_paths = event.paths
        image_data = {}
        for path in image_paths:
            with Image.open(path, "r") as image:
                buffered = BytesIO()
                image.save(
                    buffered, format="JPEG", quality=80, optimize=True, progressive=True
                )
                image_str = b64encode(buffered.getvalue())
                image_data[path] = image_str.decode("utf-8")

        json_event["images"] = image_data

    recent_events.append(event)
    send_and_append(event.id, json_event)


def broadcast_player_event(
    character: str, client: str, status: Literal["join", "leave"]
):
    event = PlayerEvent(status=status, character=character, client=client)
    broadcast(event)


def broadcast_player_list():
    event = PlayerListEvent(players=list_players())
    broadcast(event)
