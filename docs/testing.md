# TaleWeave AI Testing

## Contents

- [TaleWeave AI Testing](#taleweave-ai-testing)
  - [Contents](#contents)
  - [User Profiles](#user-profiles)
    - [Staff](#staff)
      - [Admin](#admin)
      - [Moderator](#moderator)
    - [Users](#users)
      - [Player](#player)
      - [Spectator](#spectator)
    - [Developers](#developers)
      - [ML Engineer](#ml-engineer)
      - [Project Contributor](#project-contributor)
      - [Mod Developer](#mod-developer)
  - [User Stories](#user-stories)
    - [User Stories for Staff](#user-stories-for-staff)
      - [Admin configures and runs a new server](#admin-configures-and-runs-a-new-server)
      - [Admin removes inappropriate events from the game history](#admin-removes-inappropriate-events-from-the-game-history)
    - [User Stories for Users](#user-stories-for-users)
      - [Player joins the game as a character](#player-joins-the-game-as-a-character)
      - [Player leaves the game during their turn](#player-leaves-the-game-during-their-turn)
      - [Spectator renders a recent event](#spectator-renders-a-recent-event)
    - [User Stories for Developers](#user-stories-for-developers)
      - [Mod Developer creates a new system for the game](#mod-developer-creates-a-new-system-for-the-game)
      - [Project Contributor fixes a bug in the engine](#project-contributor-fixes-a-bug-in-the-engine)

## User Profiles

### Staff

#### Admin

Goals:

- to host a game world as a Discord bot and/or website
- to set up automation, backups, and webhooks
- to set up interaction with other bots
- to moderate the world and remove inappropriate events and/or images

Skills:

- familiar with Docker containers
- familiar with JSON and YAML
- familiar with setting up Discord bots
- basic knowledge of ComfyUI and Ollama
- access to plenty of disk space and 1-2 GPUs

Notes:

- may be connected through Discord or web (mobile web should offer some admin options as well)
- could also be a player

#### Moderator

Notes:

- non-admin moderator
- TBD

### Users

#### Player

Goals:

- to play as a character in the game world
- may want to set up some automation, webhooks, or interaction between bots

Skills:

- may know some JSON
- may be familiar with scripting Discord bots and/or REST APIs

Notes:

- could be playing in Discord, web, or mobile web
- can interact with characters and items on their turn
- needs to be prompted and notified when their turn starts

#### Spectator

Goals:

- to watch the game world as events unfold
- to render and visualize recent events

Skills:

- has a Discord account and/or web browser

Notes:

- could be watching in Discord, web, or mobile web
- cannot interact with characters or items in the world
- can browse and view the world
- can render recent events

### Developers

#### ML Engineer

Goals:

- exporting prompts, actions, and results/replies as training data
- analyzing character movements, interactions, and notes to find emergent behavior

Skills:

- familiar with Python and Jupyter
- familiar with JSON, probably also YAML
- familiar with LLMs and prompting
- able to run Docker containers

#### Project Contributor

Goals:

- to add new actions and features
- to fix bugs in the game engine
- to improve the web client

Skills:

- familiar with Python and/or Typescript
- familiar with JSON and YAML
- familiar with REST and websocket APIs
- basic knowledge of Discord bots
- basic knowledge of LLMs
- able to run Docker containers
- may be familiar with React and MUI (frontend)
- may be familiar with Pydantic and other Python dependencies (backend)

#### Mod Developer

Goals:

- to develop new features as game systems
- to develop new actions and logic using existing systems

Skills:

- familiar with Python
- probably familiar with JSON and/or YAML
- basic knowledge of LLMs, especially prompting

## User Stories

### User Stories for Staff

#### Admin configures and runs a new server

> As an Admin, I want to configure a server, create a new world, and host it online so that players can join.

#### Admin removes inappropriate events from the game history

> As an Admin, I want to remove inappropriate events and images from the game history, so that players are comfortable.

### User Stories for Users

#### Player joins the game as a character

> As a Player, I want to join a running world as an existing character, so that I can act as that character.

#### Player leaves the game during their turn

> As a Player, I want to leave a running world at any time, including during my turn, so that I can go touch grass.

#### Spectator renders a recent event

> As a Spectator, I want to render a recent event from the game, so that I can visualize the characters and their actions.

### User Stories for Developers

#### Mod Developer creates a new system for the game

> As a Mod Developer, I want to write a Python module with a new game system and load it into a test world, so that I can develop custom features.

#### Project Contributor fixes a bug in the engine

> As a Project Contributor, I want to fix a bug in the game engine, so that players have a good experience.
