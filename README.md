# TailWeave AI

TaleWeave AI is an innovative open-source text adventure engine that harnesses the storytelling prowess and novel
behaviors of large language models to create a vibrant, interactive universe. This project merges the classic depth of
traditional text-based role-playing games with the cutting-edge capabilities of modern artificial intelligence,
delivering an immersive and versatile experience accessible via both Discord and web browsers.

At the core of TaleWeave AI is the AI-powered dungeon master, which not only guides narratives but also populates the
world with dynamic AI characters. These characters interact within the game environment through advanced, extensible
function calls that allow for complex, evolving scenarios. Whether you are a game developer, storyteller, or enthusiast,
TaleWeave AI empowers you to craft unique worlds, tailor adventures to your liking, and script engaging scenarios that
captivate and engage players’ imaginations.

## Features

- Cross-Platform Gameplay: Enjoy a seamless gameplay experience across Discord and web browsers, ensuring accessibility
  and continuous engagement no matter where you are.
- Rich Interactions: Dive into a world where AI-generated characters and real human players coexist, each bringing
  unique elements to the narrative and gameplay.
- Play as Any Character: Join or leave ongoing adventures without any disruption to the ongoing world, making it easy
  for players to drop in or out according to their schedules.
- AI-Driven World Generation: Leverage the capabilities of a large language model acting as your dungeon master to
  generate expansive, reactive worlds simply from a text prompt.
- Enhanced Conversations: Engage in deep, meaningful interactions with both AI and human characters, enriching your
  gaming experience with every conversation and decision.

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

## Installation

**Step 1: Clone the Repository**

```bash
git clone https://github.com/your-github-username/TaleWeaveAI.git
cd TaleWeaveAI
```

**Step 2: Set Up Your Environment**

```bash
# Install dependencies
pip install -r requirements.txt
```

**Step 3: Configuration**

- Configure the settings by editing the `config.json` file to match your setup, including Discord tokens and web server details.

**Step 4: Run the Server**

```bash
# Start the TaleWeave AI engine
python main.py
```

## Documentation

For a detailed guide on how to use TaleWeave AI, customize adventures, and integrate with Discord and web browsers,
please refer to our [Documentation](./docs). This guide includes comprehensive instructions on:

- **Setting up your first adventure:** Learn how to create and launch your own story.
- **Customizing characters:** Instructions on how to personalize AI and human characters.
- **Advanced features:** Explore the more complex functionalities of TaleWeave AI, like AI behavior tweaking and interactive scenario creation.

## Contributing

TaleWeave AI is a community-driven project, and we welcome contributions of all kinds. If you're interested in improving the engine or adding new features, please check out our contributing guidelines in [CONTRIBUTING.md](./CONTRIBUTING.md).

## Support and Community

Join our community on Discord to discuss TaleWeave AI, share your experiences, and get help from fellow users and developers. Click here to join: [TaleWeave AI Discord Community](#)

## License

TaleWeave AI is released under the MIT License. See the [LICENSE](./LICENSE) file for more details.

---

This continuation of the README provides clear instructions and necessary resources for users and contributors to effectively engage with and utilize the TaleWeave AI platform.

## TODOs

- admin panel in web UI
- store long-term memory for actors in vector DB
