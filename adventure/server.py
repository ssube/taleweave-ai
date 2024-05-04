import asyncio
from collections import deque
from json import dumps
from logging import getLogger
from threading import Thread

import websockets

from adventure.models import Actor, Room, World
from adventure.state import snapshot_world, world_json

logger = getLogger(__name__)

connected = set()
recent_events = deque(maxlen=10)
recent_world = None


async def handler(websocket):
    logger.info("Client connected")
    connected.add(websocket)

    try:
        if recent_world:
            await websocket.send(recent_world)

        for message in recent_events:
            await websocket.send(message)
    except Exception:
        logger.exception("Failed to send recent messages to new client")

    while True:
        try:
            message = await websocket.recv()
            print(message)
        except websockets.ConnectionClosedOK:
            break

    connected.remove(websocket)
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
