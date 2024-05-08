# This is an example that uses the websockets api to know when a prompt execution is done
# Once the prompt execution is done it downloads the images using the /history endpoint

import io
import json
import urllib.parse
import urllib.request
import uuid
from logging import getLogger
from os import environ, path
from random import choice, randint
from typing import List

import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from PIL import Image

logger = getLogger(__name__)

server_address = environ["COMFY_API"]
client_id = str(uuid.uuid4())


def generate_cfg():
    return randint(5, 8)


def generate_steps():
    return 30


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
    for o in history["outputs"]:
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


sizes = {
    "landscape": (1024, 768),
    "portrait": (768, 1024),
    "square": (768, 768),
}


def generate_images(
    prompt: str, count: int, size="landscape", prefix="output"
) -> List[str]:
    cfg = generate_cfg()
    width, height = sizes.get(size, (512, 512))
    steps = generate_steps()
    seed = randint(0, 10000000)
    checkpoint = choice(["diffusion-sdxl-dynavision-0-5-5-7.safetensors"])
    logger.info(
        "generating %s images at %s by %s with prompt: %s", count, width, height, prompt
    )

    # parsing here helps ensure the template emits valid JSON
    prompt_workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "seed": seed,
                "steps": steps,
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": count, "height": height, "width": width},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]},
        },
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["8", 0]},
        },
    }

    logger.debug("Connecting to Comfy API at %s", server_address)
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt_workflow)

    results = []
    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            results.append(image)

    paths: List[str] = []
    for j, image in enumerate(results):
        image_path = path.join("/home/ssube/adventure-images", f"{prefix}-{j}.png")
        with open(image_path, "wb") as f:
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="PNG")
            f.write(image_bytes.getvalue())

        paths.append(image_path)

    return paths


if __name__ == "__main__":
    paths = generate_images(
        "A painting of a beautiful sunset over a calm lake", 3, "landscape"
    )
    logger.info("Generated %d images: %s", len(paths), paths)
