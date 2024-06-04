# TaleWeave AI

TaleWeave AI is an innovative open-source text adventure engine that harnesses the storytelling prowess and novel
behaviors of large language models to create a vibrant, interactive universe. This project merges the classic depth of
traditional text-based role-playing games with the cutting-edge capabilities of modern artificial intelligence,
delivering an immersive and versatile experience accessible via both Discord and web browsers.

At the core of TaleWeave AI is the AI-powered dungeon master, which not only guides narratives but also populates the
world with dynamic AI characters. These characters interact within the game environment through advanced, extensible
function calls that allow for complex, evolving scenarios. Whether you are a game developer, storyteller, or enthusiast,
TaleWeave AI empowers you to craft unique worlds, tailor adventures to your liking, and script engaging scenarios that
captivate and engage players' imaginations.

## Contents

- [TaleWeave AI](#taleweave-ai)
  - [Contents](#contents)
  - [Features](#features)
  - [Requirements](#requirements)
    - [Recommended](#recommended)
  - [Setup](#setup)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [Support and Community](#support-and-community)
  - [License](#license)

## Features

- **Cross-Platform Gameplay**: Enjoy a seamless gameplay experience across Discord and web browsers, ensuring
  accessibility and continuous engagement no matter where you are.
- **Rich Interactions**: Dive into a world where AI-generated characters and real human players coexist, each bringing
  unique elements to the narrative and gameplay.
- **Play as Any Character**: Every character in the world is always active, powered by large language models. Human
  players can seamlessly take over AI characters, responding to system prompts and engaging in conversations with other
  characters, enhancing the depth and flexibility of interactions.
- **AI-Driven World Generation**: Leverage the capabilities of a large language model acting as your dungeon master to
  generate expansive, reactive worlds simply from a text prompt.
- **Enhanced Conversations**: Engage in deep, meaningful interactions with both AI and human characters, enriching your
  gaming experience with every conversation and decision.
- **Customizable Actions**: Introduce your own actions to interact with the world and other characters in innovative
  ways, adding a personal touch to every adventure.
- **Flexible Game Saving**: Easily save and resume your worlds at any time, preserving not only the state of the world
  but also the language model's memory to maintain continuity in your adventures.
- **Dynamic Character Behavior**: Influence characters' behavior through logical systems that simulate hunger, mood, and
  other life-like mechanics, adding layers of realism to your interactive experiences.

Emergent behavior in TaleWeave AI offers a complex and captivating layer to gameplay, as large language models (LLMs)
interpret and act on character needs and feelings with surprising depth. By incorporating function-calling capabilities,
characters driven by these models can respond to prompts like "you are hungry" combined with an "eat" action by
logically determining the need to locate and consume food. Expanding these capabilities with additional systems such as
mood and stamina further enriches character interactions. For instance, a character who is both hungry and tired may
exhibit frustration or become argumentative, reflecting a nuanced behavioral response. These layered systems interact
dynamically, creating a web of possible actions and reactions that not only enhance the realism of the game world but
also lead to unique, unpredictable narratives formed by the characters' evolving conditions and decisions.

As the AI-powered dungeon master, the large language model serves a pivotal role in TaleWeave AI, crafting not only the
overarching narratives but also the intricate details that bring the game world to life. This model excels in generating
descriptive, engaging flavor text that captures the essence of the world and its inhabitants, drawing on the same rich
data that fuels compelling storytelling in traditional text adventures. Whether it's adding intriguing twists when
characters use items or embedding subtle contextual clues into their interactions, the dungeon master ensures that each
element of the world is consistent and meaningful. By dynamically generating environments and scenarios, the dungeon
master model weaves together a coherent, immersive world where every character and their actions fit seamlessly into the
larger tapestry of the tale.

In TaleWeave AI, the logic system employs a sophisticated combination of Python and YAML to construct intricate systems
that add and modify attributes on the rooms, characters, and items in the world. Each attribute is tagged with text
labels for both first-person prompts and third-person descriptions, enabling the system to directly influence the
behaviors and responses of the language models. This architecture allows for a dynamic interaction model where the
underlying logic subtly guides the actions and reactions of the AI, enriching the narrative depth and realism of the
game environment.

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

## Contributing

TaleWeave AI is working and playable, and looking for contributors to help improve the web client, add new mechanics
and systems to the game, and fine-tune models for better role playing.

[Check out the developer pitch for more details](https://docs.google.com/presentation/d/1weHYaLzbRCq5A9K1iy33KdSvZ0bzCaBT6Trc0RCNJZE/edit?usp=sharing).

## Support and Community

Join our community on Discord to discuss TaleWeave AI, share your experiences, and get help from fellow users and
developers.

[Click here to join the TaleWeave AI Discord Community](https://discord.gg/4RfZBE77fa).

## License

TaleWeave AI is released under the MIT License. See the [LICENSE](./LICENSE) file for more details.
