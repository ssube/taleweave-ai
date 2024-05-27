# Admin's Guide to TaleWeave AI

## Contents

- [Admin's Guide to TaleWeave AI](#admins-guide-to-taleweave-ai)
  - [Contents](#contents)
  - [Hardware](#hardware)
    - [Disk space](#disk-space)
    - [GPU and VRAM](#gpu-and-vram)
    - [Networking and ports](#networking-and-ports)
  - [Setup](#setup)
    - [Clone the git repository](#clone-the-git-repository)
    - [Set up a virtual environment](#set-up-a-virtual-environment)
    - [Install the pip dependencies](#install-the-pip-dependencies)
    - [Launch Ollama for text generation](#launch-ollama-for-text-generation)
      - [Using vLLM](#using-vllm)
      - [Using OpenAI](#using-openai)
    - [Optional: Launch ComfyUI for image generation](#optional-launch-comfyui-for-image-generation)
  - [Register](#register)
    - [Register a Discord bot](#register-a-discord-bot)
    - [Invite the Discord bot](#invite-the-discord-bot)
  - [Configure](#configure)
    - [Configure the server environment](#configure-the-server-environment)
    - [Configure image generation](#configure-image-generation)
    - [Optional: Configure websocket server](#optional-configure-websocket-server)
    - [Optional: Configure world size](#optional-configure-world-size)
  - [Run](#run)
    - [Choose a world prompt or template](#choose-a-world-prompt-or-template)
    - [Launch the game](#launch-the-game)
    - [Connect and play](#connect-and-play)

## Hardware

### Disk space

The amount of disk space required depends primarily on the LLM and Stable Diffusion checkpoints being used.

The game world is usually < 1MB and up to 2 copies of each world are kept on disk. The images rendered for various
objects and events in the game can grow over time, but each image should be about 1MB, depending on the image size
that you choose.

Approximate disk space requirements:

| LLM / SD      | SD v1.5 (3-4GB) | SDXL (6-8GB) |
| ------------- | --------------- | ------------ |
| 7-8b (4-6GB)  | 8-10GB          | 10-12GB      |
| 14b (8-10GB)  | 15GB            | 20GB         |
| 30b (16-20GB) | 25GB            | 30GB         |
| 70b (30-40GB) | 35GB            | 50GB         |

The exact size will vary by model, checkpoint, quantization, etc, and is likely to grow over time.

### GPU and VRAM

Technically, you do not need a GPU to run TaleWeave AI. However, performance will be much better with at least one
GPU. Running the LLM on CPU _is not recommended_ and will impact the game's performance, but it is possible.

If you want to render images of the world while the characters are acting, you will need two GPUs or you will
need to run image generation on the CPU.

The required amount of VRAM depends on which models you choose and their memory requirements, which is related to
parameter size and quantization.

| LLM / SD | SD v1.5               | SDXL                   |
| -------- | --------------------- | ---------------------- |
| 7-8b     | 1x 16GB               | 1x 24GB or 8GB + 16GB  |
| 14b      | 1x 24GB or 8GB + 16GB | 2x 16-24GB             |
| 30b      | 1x 48GB or 8GB + 32GB | 1x 48GB or 16GB + 32GB |
| 70b*     | 8GB + 48GB            | 16GB + 48GB            |

Notes:

1. 70b models need to be quantized to 4-bit or so to run on a 48GB GPU
2. While it may be possible to run both text and image generation on the same GPU, two GPUs is recommended

### Networking and ports

If you want to make the websocket server accessible over the internet, you will need at least one open port.

If you are using a load balancer, make sure it is compatible with websockets.

## Setup

### Clone the git repository

Clone the TaleWeave AI repository:

```bash
git clone https://github.com/ssube/TaleWeaveAI.git
cd TaleWeaveAI
```

This will clone the `main` branch, which is currently the development branch and may not be totally stable.

### Set up a virtual environment

Set up a virtual environment to manage the dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

If you prefer using Conda or other tools, you can create an environment using their commands instead. Make sure they
are compatible with pip packages.

### Install the pip dependencies

Install the pip dependencies into your virtual environment:

```bash
# Install dependencies
pip install -r requirements.txt
```

### Launch Ollama for text generation

Since TaleWeave AI is a text adventure, some kind of text generator is required. By default, TaleWeave AI is designed
to work with locally-hosted LLM servers, like [Ollama](https://github.com/ollama/ollama).

Ollama releases binaries for Linux, Mac, and Windows, along with a Docker container that works on RunPod and other GPU
container services.

```shell
TODO
```

If you are using Ollama, you will need to set the following variables in your server environment:

```shell
PACKIT_DRIVER=ollama
OLLAMA_API=http://127.0.0.1:11434
```

If you are running Ollama with a GPU, you should also set the number of GPU layers and context length:

```shell
OLLAMA_NUM_GPU=100
OLLAMA_NUM_CTX=8192
```

These environment variables need to be set in the terminal where TaleWeave AI will be running, they are _not_ used by
the Ollama server.

Please see the Ollama docs for more details:

- https://github.com/ollama/ollama?tab=readme-ov-file#ollama

#### Using vLLM

You can use vLLM for text generation instead of Ollama. This has not been thoroughly tested, but anything server that
is compatible with the OpenAI API should work, and vLLM seems to work in general. Some models are available for vLLM
on the HuggingFace Hub that are not available for Ollama, and performance differs on different hardware. Use the server
that works for you.

If you are using vLLM, you will need to set the following variables in your server environment:

```shell
PACKIT_DRIVER=openai
```

Please see the vLLM docs for more details:

- https://docs.vllm.ai/en/latest/getting_started/installation.html

#### Using OpenAI

If you are using the OpenAI API, you will need to set the following variables in your server environment:

```shell
PACKIT_DRIVER=openai
```

Please see the OpenAI docs for more details:

- https://platform.openai.com/docs/quickstart

### Optional: Launch ComfyUI for image generation

Please see the ComfyUI docs for more details:

- https://github.com/comfyanonymous/ComfyUI?tab=readme-ov-file#installing

## Register

### Register a Discord bot

If you want to play the game through the Discord bot, you need to register a bot and invite it to the server(s) where
you want to play.

These bots can connect to multiple Discord servers and channels, but the bot token should be kept secret.

Visit the [Discord Developer Portal](https://discord.com/developers/applications) and create a New Application:

TODO: screenshot

On the `Bot` tab, configure the username, icon, and make sure the `Public Bot` option is checked:

TODO: screenshot

Copy the bot's token and save it to your password manager. This is effectively your bot's password and will be used
when you configure the server.

- https://discordpy.readthedocs.io/en/stable/discord.html
- https://discordjs.guide/preparations/adding-your-bot-to-servers.html#bot-invite-links

### Invite the Discord bot

Once you have the Discord bot set up, you will need to invite it to any servers where you want to play the game.

On the `OAuth2` tab, use the `URL Generator` to create an invite link.

In the `Scopes` menu, select `bot`.

TODO: screenshot

In the `Bot Permissions` menu, select `Send Messages`, `Send Messages in Threads`, and if you are rendering images,
`Attach Files`.

TODO: screenshot

Copy the `Generated URL` and paste it into your browser. The authorization screen will show a list of servers that
you can add the bot to in the `Add To Server` menu:

TODO: screenshot

Select the server where you want to play TaleWeave and click `Continue`. Make sure the permissions shown match the
ones that you selected before, then click `Authorize`.

TODO: screenshot

You should see a success page, with a redirect to the server that you chose before. You can follow this link or close
the browser and connect to Discord through the desktop or mobile apps.

## Configure

### Configure the server environment

Create a file called `.env` and add the following variables:

```shell
# ollama
PACKIT_DRIVER=ollama
PACKIT_MODEL=dolphin-llama3:70b
OLLAMA_NUM_GPU=100
OLLAMA_NUM_CTX=8192

# servers
OLLAMA_API=http://127.0.0.1:11434
DISCORD_TOKEN=YOUR_TOKEN
COMFY_API="127.0.0.1:8188"
```

### Configure image generation

Copy the `config.yml` file to a file named `custom_config.yml` and edit the `render` section to use your desired
parameters for image generation. Make sure the `checkpoints` are valid file names in your checkpoints folder. If you
provide more than one checkpoint, one will be randomly selected for each batch of images. Adjust the `sizes` as needed
to match the checkpoint and control your memory usage.

```yaml
render:
  cfg:
    min: 5
    max: 8
  checkpoints: [
    "diffusion-sdxl-dynavision-0-5-5-7.safetensors",
  ]
  path: /tmp/taleweave-images
  sizes:
    landscape:
      width: 1280
      height: 960
    portrait:
      width: 960
      height: 1280
    square:
      width: 1024
      height: 1024
  steps:
    min: 30
    max: 50
```

### Optional: Configure websocket server

_Note:_ You only need to do this step if you want to change the host or port where the websocket server will listen.

In your `custom_config.yml`, edit the `server` section to change the host and port where the websocket server will
listen for connections:

```yaml
server:
  websocket:
    host: 0.0.0.0
    port: 8001
```

Using ports < 1024 on Linux requires additional permissions. Please consider putting a load balancer like nginx in
front of the websocket server.

### Optional: Configure world size

_Note:_ You only need to do this step if you want to change the size of the world during generation.

In your `custom_config.yml`, edit the `world` section to change the size of the rooms and character inventory while
generating the world.

```yaml
world:
  size:
    character_items:
      min: 0
      max: 3
    item_effects:
      min: 0
      max: 1
    portals:
      min: 1
      max: 3
    rooms:
      min: 3
      max: 6
    room_characters:
      min: 1
      max: 3
    room_items:
      min: 0
      max: 3
```

## Run

### Choose a world prompt or template

### Launch the game

To start a game simulation using the "outback animals" example prompt and running both the Discord both and websocket
server:

```bash
# Start the TaleWeave AI engine
python3 -m taleweave.main \
  --world worlds/outback-animals-1 \
  --world-template ./taleweave/prompts.yml:outback-animals \
  --discord  \
  --server \
  --rooms 3 \
  --turns 30 \
  --optional-actions=true \
  --actions taleweave.systems.sim:init_actions \
  --systems taleweave.systems.sim:init_logic
```

This will generate a relatively small world with 3 rooms or areas, run for 30 steps, then save the game and shut down.

The world will be saved to a file named `worlds/outback-animals-1.json` and the state will be saved after each step to
another file named `worlds/outback-animals-1.state.json`. The world can be stopped at any time by pressing Ctrl-C,
although the step in progress will be lost. The saved state can be resumed and played for any number of additional
steps by running the server again with the same arguments.

> Note: `module.name:function_name` and `path/filename.yml:key` are patterns you will see repeated throughout TaleWeave AI.
> They indicate a Python module and function within it, or a data file and key within it, respectively.

The `sim_systems` provide many mechanics from popular life simulations, including hunger, thirst, exhaustion, and mood.
Custom actions and systems can be used to provide any other mechanics that are desired for your setting. The logic
system uses a combination of Python and YAML to modify the prompts connected to rooms, characters, and items in the
world, influencing the behavior of the language models.

### Connect and play
