# TaleWeave AI

TaleWeave AI is an open-source game engine designed for creating rich, immersive text adventures and multi-user dungeons
(MUDs). Play through a Discord bot or a web browser for a versatile, cross-platform gaming experience.

![TaleWeave AI logo with glowing sunrise over angular castle](https://docs-cdn.taleweave.ai/taleweave-github-1280.png)

## Features

TaleWeave AI offers a range of features for gamers, developers, and researchers. It is a:

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
- behavior experiment

TaleWeave AI does a few things out of the box:

- Generate a world from a brief text prompt
- Simulate the actions of characters in that world
- Allow humans to interact with each other and with NPCs
- Track detailed status for each entity: mood, hunger, thirst, hygiene, time of day, weather, etc
- Summarize the environment into LLM prompts
- Foster emergent behavior through action digests, shared environment, and note taking

TaleWeave AI can:

- Be modified in almost every way - everything is a plugin, including the planning-action loop that drives the simulation
- Be run locally - does not require any cloud services, but does play nicely with them
- Connect to your data - game systems can fetch data for RAG
- Export training data for fine tuning character models
- Plug in to your workflow - run the simulation step by step in Jupyter notebooks as a Python library
- Connect to your server and vice versa - the Discord bot is a plugin and can be replaced with your favorite chat platform

## Contents

- [TaleWeave AI](#taleweave-ai)
  - [Features](#features)
  - [Contents](#contents)
  - [Requirements](#requirements)
    - [Recommended](#recommended)
  - [Setup](#setup)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [Support and Community](#support-and-community)
  - [License](#license)

## Requirements

- Python 3.10
- Ollama, vLLM, or another OpenAI-compatible LLM API (including OpenAI)

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
