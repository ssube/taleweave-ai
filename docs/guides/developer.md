# Developer's Guide to TaleWeave AI

## Contents

- [Developer's Guide to TaleWeave AI](#developers-guide-to-taleweave-ai)
  - [Contents](#contents)
  - [Extending the Game](#extending-the-game)
    - [Developing Extra Actions](#developing-extra-actions)
    - [Developing Game Systems](#developing-game-systems)
  - [Modifying the Prompts](#modifying-the-prompts)
  - [Modifying the World](#modifying-the-world)
    - [Using the World Editor](#using-the-world-editor)
    - [Creating New Worlds](#creating-new-worlds)
    - [Modifying Existing Worlds](#modifying-existing-worlds)

## Extending the Game

There are two primary ways to extend TaleWeave AI: extra actions and new game systems.

Extra actions offer characters new ways to interact with the world or give administrators new ways to control the world.

Game systems can add new game mechanics, logical systems, and even new stages during each turn. All of the base game
mechanics are implemented using optional systems - you can disable the planning and action stages, if you want.

### Developing Extra Actions

Actions are Python functions using the Langchain tool calling mechanism and OpenAI tool JSON schema.

### Developing Game Systems

Game systems can provide callbacks to:

- `format` entity attributes to be added to their prompt
- `generate` attributes and other data for the system
- `initialize` the system's data
- `simulate` the system on each turn

## Modifying the Prompts

TaleWeave AI ships with prompts that are compatible with most Llama-based models, but you may want to use custom
prompts if you are using models that use a different prompt style or were trained in a different language.

## Modifying the World

### Using the World Editor

TaleWeave AI comes with a basic command-line world editor that can be used to add, remove, and modify entities in
your game worlds and saved states.

### Creating New Worlds

TaleWeave AI worlds are stored in human-readable markup languages, usually JSON or YAML. You can create new worlds
using the world editor or your favorite text editor.

You can use the JSON schema for the `World` entity to generate new worlds using models that understand JSON schemas
or tools like `outlines`.

Prompts for ChatGPT and similar models:

> Characters:
>
> - Alice
> - Bob
>
> Rooms:
>
> - House
> - Office
>
> Remember these lists and help generate each room, one by one, based on the following schema.
> I will prompt you for each room. Do not generate any rooms until prompted.
> Generate one room for each prompt, and include some characters. Only include each character in one room, do not reuse characters.

Followed by:

> Generate the "House" room based on this JSON schema.

Upload the `schema/room.json` file along with the last prompt.

To generate more rooms:

> Generate another room using the same JSON schema. Generate the "Office" room.

If the model starts to forget the schema, upload the prompt again and alternate prompts as needed.

### Modifying Existing Worlds
