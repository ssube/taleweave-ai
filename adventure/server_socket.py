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

from adventure.context import broadcast, get_actor_agent_for_name, set_actor_agent
from adventure.models.entity import Actor, Item, Room, World
from adventure.models.event import (
    GameEvent,
    PlayerEvent,
    PlayerListEvent,
    PromptEvent,
    RenderEvent,
)
from adventure.player import (
    RemotePlayer,
    get_player,
    has_player,
    list_players,
    remove_player,
    set_player,
)
from adventure.render_comfy import render_event
from adventure.state import snapshot_world, world_json

logger = getLogger(__name__)

connected = set()
recent_events: MutableSequence[GameEvent] = deque(maxlen=100)
recent_json: MutableSequence[str] = deque(maxlen=100)
last_snapshot = None
player_names: Dict[str, str] = {}


def get_player_name(client_id: str) -> str:
    return player_names.get(client_id, client_id)


async def handler(websocket):
    id = uuid4().hex
    logger.info("Client connected, given id: %s", id)
    connected.add(websocket)

    async def next_turn(character: str, prompt: str) -> None:
        await websocket.send(
            dumps(
                {
                    "type": "prompt",
                    "client": id,
                    "character": character,
                    "prompt": prompt,
                    "actions": [],
                }
            ),
        )

    def sync_turn(event: PromptEvent) -> bool:
        player = get_player(id)
        if player and player.name == event.actor.name:
            asyncio.run(next_turn(event.actor.name, event.prompt))
            return True

        return False

    try:
        await websocket.send(dumps({"type": "id", "client": id}))

        # TODO: only send this if the recent events don't contain a snapshot
        if last_snapshot and last_snapshot not in recent_json:
            await websocket.send(last_snapshot)

        for message in recent_json:
            await websocket.send(message)
    except Exception:
        logger.exception("Failed to send recent messages to new client")

    while True:
        try:
            # if this socket is attached to a character and that character's turn is active, wait for input
            message = await websocket.recv()
            player_name = get_player_name(id)
            logger.info(f"Received message for {player_name}: {message}")

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
                                f"Name {new_player_name} is already in use by {existing_id}"
                            )
                            continue

                        logger.info(
                            f"changing player name for {id} to {new_player_name}"
                        )
                        player_names[id] = new_player_name

                    elif "become" in data:
                        character_name = data["become"]
                        if has_player(character_name):
                            logger.error(
                                f"Character {character_name} is already in use"
                            )
                            continue

                        # TODO: should this always remove?
                        remove_player(id)

                        actor, llm_agent = get_actor_agent_for_name(character_name)
                        if not actor:
                            logger.error(f"Failed to find actor {character_name}")
                            continue

                        # prevent any recursive fallback bugs
                        if isinstance(llm_agent, RemotePlayer):
                            logger.warning(
                                "patching recursive fallback for %s", character_name
                            )
                            llm_agent = llm_agent.fallback_agent

                        player = RemotePlayer(
                            actor.name,
                            actor.backstory,
                            sync_turn,
                            fallback_agent=llm_agent,
                        )
                        set_player(id, player)
                        logger.info(
                            f"Client {player_name} is now character {character_name}"
                        )

                        # swap out the LLM agent
                        set_actor_agent(actor.name, actor, player)

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
                    event_id = data["event"]
                    event = next((e for e in recent_events if e.id == event_id), None)
                    if event:
                        render_event(event)
                    else:
                        logger.error(f"Failed to find event {event_id}")

            except Exception:
                logger.exception("Failed to parse message")
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

        actor, _ = get_actor_agent_for_name(player.name)
        if actor and player.fallback_agent:
            logger.info("restoring LLM agent for %s", player.name)
            set_actor_agent(player.name, actor, player.fallback_agent)

    logger.info("client disconnected: %s", id)


socket_thread = None


def server_json(obj):
    if isinstance(obj, (Actor, Item, Room)):
        return obj.name

    return world_json(obj)


def send_and_append(id: str, message: Dict):
    json_message = dumps(message, default=server_json)
    recent_json.append(json_message)
    websockets.broadcast(connected, json_message)
    return json_message


def launch_server():
    global socket_thread

    def run_sockets():
        asyncio.run(server_main())

    socket_thread = Thread(target=run_sockets, daemon=True)
    socket_thread.start()

    return [socket_thread]


async def server_main():
    async with websockets.serve(handler, "", 8001):
        logger.info("Server started")
        await asyncio.Future()  # run forever


def server_system(world: World, step: int):
    global last_snapshot
    id = uuid4().hex  # TODO: should a server be allowed to generate event IDs?
    json_state = {
        **snapshot_world(world, step),
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
