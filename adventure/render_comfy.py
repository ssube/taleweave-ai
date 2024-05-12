import io
import json
import urllib.parse
import urllib.request
from logging import getLogger
from os import environ, path
from queue import Queue
from random import choice, randint
from threading import Thread
from typing import List
from uuid import uuid4

import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

from adventure.context import broadcast
from adventure.models.config import Range, RenderConfig, Size
from adventure.models.entity import WorldEntity
from adventure.models.event import (
    ActionEvent,
    GameEvent,
    RenderEvent,
    ReplyEvent,
    ResultEvent,
    StatusEvent,
)

logger = getLogger(__name__)

server_address = environ["COMFY_API"]
client_id = uuid4().hex
render_config: RenderConfig = RenderConfig(
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
)


# requests to generate images for game events
render_queue: Queue[GameEvent | WorldEntity] = Queue()
render_thread: Thread | None = None


def generate_cfg():
    if render_config.cfg.min == render_config.cfg.max:
        return render_config.cfg.min

    return randint(render_config.cfg.min, render_config.cfg.max)


def generate_steps():
    if render_config.steps.min == render_config.steps.max:
        return render_config.steps.min

    return randint(render_config.steps.min, render_config.steps.max)


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


def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)["prompt_id"]
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # Execution is done
        else:
            continue  # previews are binary data

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
    cfg = generate_cfg()
    dims = render_config.sizes[size]
    steps = generate_steps()
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
        loader=FileSystemLoader(["adventure/templates"]),
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
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id), timeout=60)
    images = get_images(ws, prompt_workflow)

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


def prompt_from_event(event: GameEvent) -> str | None:
    if isinstance(event, ActionEvent):
        if event.item:
            return f"{event.actor.name} uses the {event.item.name}. {event.item.description}. {event.actor.description}. {event.room.description}."

        return f"{event.actor.name} {event.action}. {event.actor.description}. {event.room.description}."

    if isinstance(event, ReplyEvent):
        return event.text

    if isinstance(event, ResultEvent):
        return f"{event.result}. {event.actor.description}. {event.room.description}."

    if isinstance(event, StatusEvent):
        if event.room:
            if event.actor:
                return f"{event.text}. {event.actor.description}. {event.room.description}."

            return f"{event.text}. {event.room.description}."

        return event.text

    return None


def prompt_from_entity(entity: WorldEntity) -> str:
    return entity.description


def get_image_prefix(event: GameEvent | WorldEntity) -> str:
    if isinstance(event, ActionEvent):
        return f"event-action-{event.actor.name}-{event.action}"

    if isinstance(event, ReplyEvent):
        return f"event-reply-{event.actor.name}"

    if isinstance(event, ResultEvent):
        return f"event-result-{event.actor.name}"

    if isinstance(event, StatusEvent):
        return "status"

    if isinstance(event, WorldEntity):
        return f"entity-{event.__class__.__name__.lower()}-{event.name}"

    return "unknown"


def render_loop():
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
            broadcast(RenderEvent(paths=existing_images, source=event))
            continue

        # generate the prompt
        if isinstance(event, WorldEntity):
            logger.info("rendering entity %s", event)
            prompt = prompt_from_entity(event)
        else:
            logger.info("rendering event %s", event)
            prompt = prompt_from_event(event)

        # render or not
        if prompt:
            logger.info("rendering prompt for event %s: %s", event, prompt)
            image_paths = generate_images(prompt, 2, prefix=prefix)
            broadcast(RenderEvent(paths=image_paths, source=event))
        else:
            logger.warning("no prompt for event %s", event)


def render_entity(entity: WorldEntity):
    render_queue.put(entity)


def render_event(event: GameEvent):
    render_queue.put(event)


def launch_render(config: RenderConfig):
    global render_config
    global render_thread

    # update the config
    logger.info("updating render config: %s", config)
    render_config = config

    # start the render thread
    logger.info("launching render thread")
    render_thread = Thread(target=render_loop, daemon=True)
    render_thread.start()

    return [render_thread]


if __name__ == "__main__":
    paths = generate_images(
        "A painting of a beautiful sunset over a calm lake", 3, "landscape"
    )
    logger.info("Generated %d images: %s", len(paths), paths)
