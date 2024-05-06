import asyncio
from collections import deque
from json import dumps, loads
from logging import getLogger
from threading import Thread
from typing import Dict, Literal
from uuid import uuid4

import websockets

from adventure.context import get_actor_agent_for_name, set_actor_agent_for_name
from adventure.models import Actor, Room, World
from adventure.player import RemotePlayer
from adventure.state import snapshot_world, world_json

logger = getLogger(__name__)

connected = set()
characters: Dict[str, RemotePlayer] = {}
recent_events = deque(maxlen=100)
recent_world = None


async def handler(websocket):
    id = uuid4().hex
    logger.info("Client connected, given id: %s", id)
    connected.add(websocket)

    async def next_turn(character: str, prompt: str) -> None:
        await websocket.send(
            dumps(
                {
                    "type": "prompt",
                    "id": id,
                    "character": character,
                    "prompt": prompt,
                    "actions": [],
                }
            ),
        )

    def sync_turn(character: str, prompt: str) -> bool:
        if id not in characters:
            return False

        asyncio.run(next_turn(character, prompt))
        return True

    try:
        await websocket.send(dumps({"type": "id", "id": id}))

        if recent_world:
            await websocket.send(recent_world)

        for message in recent_events:
            await websocket.send(message)
    except Exception:
        logger.exception("Failed to send recent messages to new client")

    while True:
        try:
            # if this socket is attached to a character and that character's turn is active, wait for input
            message = await websocket.recv()
            logger.info(f"Received message for {id}: {message}")

            try:
                data = loads(message)
                message_type = data.get("type", None)
                if message_type == "player":
                    character = characters.get(id)
                    if character:
                        del characters[id]

                    character_name = data["become"]
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

                    if character_name in [
                        player.name for player in characters.values()
                    ]:
                        logger.error(f"Character {character_name} is already in use")
                        continue

                    # player_name = data["player"]
                    player = RemotePlayer(
                        actor.name, actor.backstory, sync_turn, fallback_agent=llm_agent
                    )
                    characters[id] = player
                    logger.info(f"Client {id} is now character {character_name}")

                    # swap out the LLM agent
                    set_actor_agent_for_name(actor.name, actor, player)

                    # notify all clients that this character is now active
                    player_event(character_name, id, "join")
                    player_list()
                elif message_type == "input" and id in characters:
                    player = characters[id]
                    logger.info("queueing input for player %s: %s", player.name, data)
                    player.input_queue.put(data["input"])

            except Exception:
                logger.exception("Failed to parse message")
        except websockets.ConnectionClosedOK:
            break

    connected.remove(websocket)

    # swap out the character for the original agent when they disconnect
    if id in characters:
        player = characters[id]
        del characters[id]

        logger.info("Disconnecting player for %s", player.name)
        player_event(player.name, id, "leave")
        player_list()

        actor, _ = get_actor_agent_for_name(player.name)
        if actor and player.fallback_agent:
            logger.info("Restoring LLM agent for %s", player.name)
            set_actor_agent_for_name(player.name, actor, player.fallback_agent)

    logger.info("Client disconnected: %s", id)


socket_thread = None
static_thread = None


def server_json(obj):
    if isinstance(obj, Actor):
        return obj.name

    if isinstance(obj, Room):
        return obj.name

    return world_json(obj)


def send_and_append(message):
    json_message = dumps(message, default=server_json)
    recent_events.append(json_message)
    websockets.broadcast(connected, json_message)
    return json_message


def launch_server():
    global socket_thread, static_thread

    def run_sockets():
        asyncio.run(server_main())

    socket_thread = Thread(target=run_sockets)
    socket_thread.start()


async def server_main():
    async with websockets.serve(handler, "", 8001):
        logger.info("Server started")
        await asyncio.Future()  # run forever


def server_system(world: World, step: int):
    global recent_world
    json_state = {
        **snapshot_world(world, step),
        "type": "world",
    }
    recent_world = send_and_append(json_state)


def server_result(room: Room, actor: Actor, action: str):
    json_action = {
        "actor": actor,
        "result": action,
        "room": room,
        "type": "result",
    }
    send_and_append(json_action)


def server_action(room: Room, actor: Actor, message: str):
    json_input = {
        "actor": actor,
        "input": message,
        "room": room,
        "type": "action",
    }
    send_and_append(json_input)


def server_event(message: str):
    json_broadcast = {
        "message": message,
        "type": "event",
    }
    send_and_append(json_broadcast)


def player_event(character: str, id: str, event: Literal["join", "leave"]):
    json_broadcast = {
        "type": "player",
        "character": character,
        "id": id,
        "event": event,
    }
    send_and_append(json_broadcast)


def player_list():
    json_broadcast ={
        "type": "players",
        "players": {player.name: player_id for player_id, player in characters.items()},
    }
    send_and_append(json_broadcast)
