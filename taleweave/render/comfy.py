import io
import json
import urllib.parse
import urllib.request
from logging import getLogger
from os import environ, path
from queue import Queue
from random import choice, randint
from re import sub
from threading import Thread
from typing import List

import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from fnvhash import fnv1a_32
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

from taleweave.context import broadcast, get_game_config
from taleweave.models.base import IntRange, uuid
from taleweave.models.config import RenderConfig
from taleweave.models.entity import WorldEntity
from taleweave.models.event import (
    ActionEvent,
    GameEvent,
    GenerateEvent,
    RenderEvent,
    ReplyEvent,
    ResultEvent,
    StatusEvent,
)
from taleweave.utils.random import resolve_int_range

from .prompt import prompt_from_entity, prompt_from_event

logger = getLogger(__name__)

server_address = environ["COMFY_API"]
client_id = uuid()


# requests to generate images for game events
render_queue: Queue[GameEvent | WorldEntity] = Queue()
render_thread: Thread | None = None


def get_render_config():
    config = get_game_config()
    return config.render


def generate_cfg(cfg: int | IntRange):
    return resolve_int_range(cfg)


def generate_steps(steps: int | IntRange):
    return resolve_int_range(steps)


def generate_batches(
    count: int,
    batch_size: int = 3,
) -> List[int]:
    """
    Generate count images in batches of at most batch_size.
    """

    batches = []
    for i in range(0, count, batch_size):
        batches.append(min(count - i, batch_size))

    return batches


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(
        "http://{}/view?{}".format(server_address, url_values)
    ) as response:
        return response.read()


def get_history(prompt_id):
    with urllib.request.urlopen(
        "http://{}/history/{}".format(server_address, prompt_id)
    ) as response:
        return json.loads(response.read())


def get_images(ws_host, prompt, max_retries=3):
    prompt_id = queue_prompt(prompt)["prompt_id"]
    output_images = {}
    retry = 0

    ws = websocket.WebSocket()
    ws.connect(ws_host, timeout=60)
    while True:
        try:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message["type"] == "executing":
                    data = message["data"]
                    if data["node"] is None and data["prompt_id"] == prompt_id:
                        break  # Execution is done
            else:
                continue  # previews are binary data
        except websocket._exceptions.WebSocketTimeoutException:
            logger.warning("timeout while waiting for image data")
            retry += 1
            if retry >= max_retries:
                logger.error("max retries exceeded, giving up")
                break
            else:
                # reconnect
                ws = websocket.WebSocket()
                ws.connect(ws_host, timeout=60)
                continue

    history = get_history(prompt_id)[prompt_id]
    for _ in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                images_output = []
                for image in node_output["images"]:
                    image_data = get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images


def generate_image_tool(prompt, count, size="landscape"):
    output_paths = []
    for i, count in enumerate(generate_batches(count)):
        results = generate_images(prompt, count, size, prefix=f"output-{i}")
        output_paths.extend(results)

    return output_paths


def generate_images(
    prompt: str, count: int, size="landscape", prefix="output"
) -> List[str]:
    render_config = get_render_config()
    cfg = generate_cfg(render_config.cfg)
    dims = render_config.sizes[size]
    steps = generate_steps(render_config.steps)
    seed = randint(0, 10000000)
    checkpoint = choice(render_config.checkpoints)
    logger.info(
        "generating %s images at %s by %s with prompt: %s",
        count,
        dims.width,
        dims.height,
        prompt,
    )

    env = Environment(
        loader=FileSystemLoader(["taleweave/templates"]),
        autoescape=select_autoescape(["json"]),
    )
    template = env.get_template("comfy.json.j2")
    result = template.render(
        cfg=cfg,
        height=dims.height,
        width=dims.width,
        steps=steps,
        seed=seed,
        checkpoint=checkpoint,
        prompt=prompt.replace("\n", ". "),
        negative_prompt="",
        count=count,
        prefix=prefix,
    )

    # parsing here helps ensure the template emits valid JSON
    logger.debug("template workflow: %s", result)
    prompt_workflow = json.loads(result)

    logger.debug("connecting to Comfy API at %s", server_address)
    images = get_images(
        "ws://{}/ws?clientId={}".format(server_address, client_id), prompt_workflow
    )

    results = []
    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            results.append(image)

    paths: List[str] = []
    for j, image in enumerate(results):
        image_path = path.join(render_config.path, f"{prefix}-{j}.png")
        with open(image_path, "wb") as f:
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="PNG")
            f.write(image_bytes.getvalue())

        paths.append(image_path)

    return paths


def sanitize_name(name: str) -> str:
    def valid_char(c: str) -> str:
        if c.isalnum() or c in ["-", "_"]:
            return c

        return "-"

    valid_name = "".join([valid_char(c) for c in name])
    valid_name = sub(r"-+", "-", valid_name)
    valid_name = valid_name.strip("-").strip("_").strip()
    return valid_name.lower()


def fast_hash(text: str) -> str:
    return hex(fnv1a_32(text.encode("utf-8")))


def get_image_prefix(event: GameEvent | WorldEntity) -> str:
    if isinstance(event, ActionEvent):
        return sanitize_name(f"event-action-{event.character.name}-{event.action}")

    if isinstance(event, ReplyEvent):
        return sanitize_name(
            f"event-reply-{event.speaker.name}-{fast_hash(event.text)}"
        )

    if isinstance(event, ResultEvent):
        return sanitize_name(
            f"event-result-{event.character.name}-{fast_hash(event.result)}"
        )

    if isinstance(event, StatusEvent):
        return sanitize_name(f"event-status-{fast_hash(event.text)}")

    if isinstance(event, WorldEntity):
        return sanitize_name(f"entity-{event.__class__.__name__.lower()}-{event.name}")

    return "unknown"


def render_loop():
    render_config = get_render_config()

    while True:
        event = render_queue.get()
        prefix = get_image_prefix(event)

        # check if images already exist
        image_index = 0
        image_path = path.join(render_config.path, f"{prefix}-{image_index}.png")
        existing_images = []
        while path.exists(image_path):
            existing_images.append(image_path)
            image_index += 1
            image_path = path.join(render_config.path, f"{prefix}-{image_index}.png")

        if existing_images:
            logger.info(
                "using existing images for event %s: %s", event, existing_images
            )

            if isinstance(event, WorldEntity):
                title = event.name  # TODO: generate a real title
            else:
                title = event.type

            broadcast(
                RenderEvent(
                    paths=existing_images,
                    prompt="reusing existing images",
                    source=event,
                    title=title,
                )
            )
            continue

        # generate the prompt
        if isinstance(event, WorldEntity):
            logger.info("rendering entity %s", event.name)
            prompt = prompt_from_entity(event)
            title = event.name  # TODO: generate a real title
        else:
            logger.info("rendering event %s", event.id)
            prompt = prompt_from_event(event)
            title = event.type  # TODO: generate a real title

        # render or not
        if prompt:
            logger.debug("rendering prompt for event %s: %s", event, prompt)
            image_paths = generate_images(prompt, render_config.count, prefix=prefix)
            broadcast(
                RenderEvent(paths=image_paths, prompt=prompt, source=event, title=title)
            )
        else:
            logger.warning("no prompt for event %s", event)


def render_entity(entity: WorldEntity):
    render_queue.put(entity)


def render_event(event: GameEvent):
    render_queue.put(event)


def render_generated(event: GameEvent):
    if isinstance(event, GenerateEvent) and event.entity:
        logger.info("rendering generated entity: %s", event.entity.name)
        render_entity(event.entity)


def launch_render(config: RenderConfig):
    global render_thread

    # start the render thread
    logger.info("launching render thread")
    render_thread = Thread(target=render_loop, daemon=True)
    render_thread.start()

    return [render_thread]


if __name__ == "__main__":
    paths = generate_images(
        "A painting of a beautiful sunset over a calm lake", 3, "landscape"
    )
    logger.info("generated %d images: %s", len(paths), paths)
