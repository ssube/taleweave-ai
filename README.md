# TaleWeave AI

TaleWeave AI is an open-source game engine designed for creating rich, immersive text adventures and multi-user dungeons
(MUDs). Play through a Discord bot or a web browser for a versatile, cross-platform gaming experience.

![TaleWeave AI logo with glowing sunrise over angular castle](https://docs-cdn.taleweave.ai/taleweave-github-1280.png)

## Contents

- [TaleWeave AI](#taleweave-ai)
  - [Contents](#contents)
  - [Features](#features)
    - [Game Actions](#game-actions)
    - [Game Systems](#game-systems)
  - [Requirements](#requirements)
    - [Recommended](#recommended)
  - [Setup](#setup)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [Support and Community](#support-and-community)
  - [License](#license)

## Features

TaleWeave AI is meant for gamers, developers, and researchers. It is a:

- multiplayer text adventure
- Discord role-playing game
- emergent behavior laboratory
- life simulator
- survival game
- game engine
- world generator
- human-machine interface
- multi-user dungeon
- cross-platform gaming experience
- behavioral experiment

TaleWeave AI does a few things out of the box:

- Generate a world from a brief text prompt
- Simulate the actions of characters in that world
- Allow humans to interact with each other and with NPCs
- Track detailed status for each entity: mood, hunger, thirst, hygiene, weather, and more
- Summarize the environment into LLM prompts
- Foster emergent behavior through action digests, shared environment, and note taking

TaleWeave AI can:

- Be modified in almost every way - everything is a plugin, including the planning and action stages that drive the simulation
- Be run locally - does not require any cloud services, but does play nicely with them
- Connect to your data - game systems can fetch data for RAG, making responses richer and more consistent
- Export training data - for analysis, visualization, and fine tuning of character models
- Plug in to your workflow - run the simulation step by step in Jupyter notebooks using the TaleWeave AI engine as a Python library
- Connect to your server and vice versa - the Discord bot is a plugin and can be replaced with your favorite chat platform

### Game Actions

TaleWeave AI has in-game actions for:

| Core         | Life Sim        | RPG       |
| ------------ | --------------- | --------- |
| Planning     | Hunger & Thirst | Combat    |
| Conversation | Hygiene         | Crafting  |
| Movement     | Sleeping        | Magic     |
| Exploration  |                 | Movement* |
|              |                 | Writing   |

1. The core exploration actions provide ways for characters to expand the world by finding new rooms and items.
2. The RPG movement actions provide additional situational movement like crawling, climbing, and jumping.

### Game Systems

TaleWeave AI has game systems for:

| Core     | Life Sim        | RPG    | Environment |
| -------- | --------------- | ------ | ----------- |
| Acting   | Hunger & Thirst | Health | Humidity    |
| Planning | Hygiene         | Quests | Temperature |
| Summary  | Mood            |        | Time of day |
|          | Sleeping        |        | Weather     |

1. The core summary system provides character with a summary of actions taken by other characters in between turns.

All of the game systems are optional, including the core systems, so you can configure a world where characters only
plan and never act, or vice versa.

## Requirements

- Python 3.10+
- Ollama or an OpenAI-compatible LLM API like llama.cpp, vLLM, or OpenAI

While TaleWeave AI can be run entirely on CPU, one or more GPUs are highly recommended.

### Recommended

- 1-2 16GB or larger GPUs
- ComfyUI
- Discord account

## Setup

Please [see the admin guide for setup instructions](./docs/guides/admin.md).

TaleWeave AI is provided as both a Python module and a Docker container. [Everything can be run
locally](./docs/guides/admin.md#running-locally) or [run on a container host like
RunPod](./docs/guides/admin.md#running-on-runpod).

## Documentation

For a detailed guide on how to use TaleWeave AI, customize adventures, and integrate with Discord and web browsers,
please check out to [the documentation folder](./docs).

Detailed guides are available for:

- [admins](./docs/guides/admin.md)
- [game developers](./docs/guides/developer.md)
- [players](./docs/guides/player.md)

## Contributing

TaleWeave AI is working, playable, and looking for contributors. We need developers to help improve the web client, add
new mechanics and systems to the game, and fine-tune models for better role playing.

[Check out the developer pitch for more details](https://docs.google.com/presentation/d/1weHYaLzbRCq5A9K1iy33KdSvZ0bzCaBT6Trc0RCNJZE/edit?usp=sharing).

## Support and Community

Join our community on Discord to discuss TaleWeave AI, share your experiences, and get help from fellow users and
developers.

[Click here to join the TaleWeave AI Discord Community](https://discord.gg/4RfZBE77fa).

## License

TaleWeave AI is released under the MIT License. See the [LICENSE](./LICENSE) file for more details.
