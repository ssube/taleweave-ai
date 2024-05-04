import asyncio
from json import dumps
from logging import getLogger
from threading import Thread

import websockets
from flask import Flask, send_from_directory

from adventure.models import Actor, Room, World
from adventure.state import snapshot_world, world_json

logger = getLogger(__name__)

app = Flask(__name__)
connected = set()


@app.route("/<path:page>")
def send_report(page: str):
    print(f"Sending {page}")
    return send_from_directory(
        "/home/ssube/code/github/ssube/llm-adventure/web-ui", page
    )


async def handler(websocket):
    connected.add(websocket)
    while True:
        try:
            # await websocket.wait_closed()
            message = await websocket.recv()
            print(message)
        except websockets.ConnectionClosedOK:
            break

    connected.remove(websocket)


socket_thread = None
static_thread = None


def launch_server():
    global socket_thread, static_thread

    def run_sockets():
        asyncio.run(server_main())

    def run_static():
        app.run(port=8000)

    socket_thread = Thread(target=run_sockets)
    socket_thread.start()

    static_thread = Thread(target=run_static)
    static_thread.start()


async def server_main():
    async with websockets.serve(handler, "", 8001):
        logger.info("Server started")
        await asyncio.Future()  # run forever


def server_system(world: World, step: int):
    json_state = {
        **snapshot_world(world, step),
        "type": "world",
    }
    websockets.broadcast(connected, dumps(json_state, default=world_json))


def server_result(room: Room, actor: Actor, action: str):
    json_action = {
        "actor": actor.name,
        "result": action,
        "room": room.name,
        "type": "result",
    }
    websockets.broadcast(connected, dumps(json_action))


def server_input(room: Room, actor: Actor, message: str):
    json_input = {
        "actor": actor.name,
        "input": message,
        "room": room.name,
        "type": "input",
    }
    websockets.broadcast(connected, dumps(json_input))
