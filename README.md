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
  - [Installation](#installation)
    - [Step 1: Clone the Repository](#step-1-clone-the-repository)
    - [Step 2: Set Up Your Environment](#step-2-set-up-your-environment)
    - [Step 3: Configuration](#step-3-configuration)
    - [Step 4: Run the Dependencies](#step-4-run-the-dependencies)
    - [Step 5: Launch the Game Server](#step-5-launch-the-game-server)
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

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ssube/TaleWeaveAI.git
cd TaleWeaveAI
```

### Step 2: Set Up Your Environment

```bash
# Create a virtual environment
python3 -m venv venv
# Load the virtual environment
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configuration

Configure the settings by editing the `.env` file to match your setup, including Discord tokens and web server details.

### Step 4: Run the Dependencies

Launch Comfy UI for image generation and Ollama for text generation.

### Step 5: Launch the Game Server

To start a game simulation using the "outback animals" example prompt and running both the Discord both and websocket
server:

```bash
# Start the TaleWeave AI engine
python3 -m taleweave.main \
  --world worlds/outback-animals-1 \
  --world-prompt ./taleweave/prompts.yml:outback-animals \
  --discord=true  \
  --server=true \
  --rooms 3 \
  --turns 30 \
  --optional-actions=true \
  --actions taleweave.systems.sim:init_actions \
  --systems taleweave.systems.sim:init_logic
```

This will generate a relatively small world with 3 rooms or areas, run for 30 steps, then shut down.

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

## Documentation

For a detailed guide on how to use TaleWeave AI, customize adventures, and integrate with Discord and web browsers,
please refer to our [Documentation](./docs). This guide includes comprehensive instructions on:

## Contributing

TaleWeave AI is a community-driven project, and we welcome contributions of all kinds. If you're interested in improving
the engine or adding new features, please check out our contributing guidelines in [CONTRIBUTING.md](./CONTRIBUTING.md).

## Support and Community

Join our community on Discord to discuss TaleWeave AI, share your experiences, and get help from fellow users and
developers. Click here to join: [TaleWeave AI Discord Community](#)

## License

TaleWeave AI is released under the MIT License. See the [LICENSE](./LICENSE) file for more details.
