import asyncio
from collections import deque
from json import dumps, loads
from logging import getLogger
from threading import Thread
from typing import Dict, Tuple

import websockets

from adventure.context import get_actor_agent_for_name
from adventure.models import Actor, Room, World
from adventure.player import RemotePlayer
from adventure.state import snapshot_world, world_json

logger = getLogger(__name__)

connected = set()
characters: Dict[str, RemotePlayer] = {}
recent_events = deque(maxlen=100)
recent_world = None


async def handler(websocket):
    logger.info("Client connected")
    connected.add(websocket)

    async def next_turn(character: str, prompt: str) -> None:
        await websocket.send(connected, dumps({
            "type": "turn",
            "character": character,
            "prompt": prompt,
        }))

    def sync_turn(character: str, prompt: str) -> bool:
        if websocket not in characters:
            return False

        asyncio.run(next_turn(character, prompt))
        return True

    try:
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
            logger.info(f"Received message: {message}")

            try:
                data = loads(message)
                if "become" in data:
                    character = characters.get(websocket)
                    if character:
                        del characters[websocket]

                    character_name = data["become"]
                    actor, _ = get_actor_agent_for_name(character_name)
                    if not actor:
                        logger.error(f"Failed to find actor {character_name}")
                        continue

                    if character_name in [player.name for player in characters.values()]:
                        logger.error(f"Character {character_name} is already in use")
                        continue

                    characters[websocket] = RemotePlayer(actor.name, actor.backstory, sync_turn)
                    logger.info(f"Client {websocket} is now character {character_name}")
                elif websocket in characters:
                    player = characters[websocket]
                    player.input_queue.put(message)

            except Exception:
                logger.exception("Failed to parse message")
        except websockets.ConnectionClosedOK:
            break

    connected.remove(websocket)

    # TODO: swap out the character for the original agent
    if websocket in characters:
        del characters[websocket]

    logger.info("Client disconnected")


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
