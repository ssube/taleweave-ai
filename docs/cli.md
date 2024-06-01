# TaleWeave AI Command Line Options

The following command line arguments are available when launching the TaleWeave AI engine:

- **--actions**
  - **Type:** String
  - **Description:** Additional actions to include in the simulation. Note: More than one argument is allowed.

- **--add-rooms**
  - **Type:** Integer
  - **Default:** 0
  - **Description:** The number of new rooms to generate before starting the simulation.

- **--config**
  - **Type:** String
  - **Description:** The file to load additional configuration from.

- **--discord**
  - **Action:** No options are needed for this argument. Simply passing the argument name is enough to enable this option.
  - **Description:** Run the simulation in a Discord bot.

- **--flavor**
  - **Type:** String
  - **Default:** ""
  - **Description:** Additional flavor text for the generated world.

- **--optional-actions**
  - **Action:** No options are needed for this argument. Simply passing the argument name is enough to enable this option.
  - **Description:** Include optional actions in the simulation.

- **--player**
  - **Type:** String
  - **Description:** The name of the character to play as.

- **--prompts**
  - **Type:** String
  - **Description:** The file to load game prompts from. Note: More than one argument is allowed.

- **--render**
  - **Action:** No options are needed for this argument. Simply passing the argument name is enough to enable this option.
  - **Description:** Run the render thread.

- **--render-generated**
  - **Action:** No options are needed for this argument. Simply passing the argument name is enough to enable this option.
  - **Description:** Render entities as they are generated.

- **--rooms**
  - **Type:** Integer
  - **Description:** The number of rooms to generate.

- **--server**
  - **Action:** No options are needed for this argument. Simply passing the argument name is enough to enable this option.
  - **Description:** Run the websocket server.

- **--state**
  - **Type:** String
  - **Description:** The file to save the world state to. Defaults to `$world.state.json` if not set.

- **--turns**
  - **Type:** Integer or "inf"
  - **Default:** 10
  - **Description:** The number of simulation turns to run.

- **--systems**
  - **Type:** String
  - **Description:** Extra systems to run in the simulation. Note: More than one argument is allowed.

- **--theme**
  - **Type:** String
  - **Default:** "fantasy"
  - **Description:** The theme of the generated world.

- **--world**
  - **Type:** String
  - **Default:** "world"
  - **Description:** The file to save the generated world to.

- **--world-template**
  - **Type:** String
  - **Description:** The template file to load the world prompt from.