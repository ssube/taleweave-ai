# Dev Guide

## Contents

- [Dev Guide](#dev-guide)
  - [Contents](#contents)
  - [Configuration](#configuration)
    - [Why so many configuration sources?](#why-so-many-configuration-sources)
  - [Engine Notes](#engine-notes)
  - [FAQ](#faq)
  - [TODOs](#todos)

## Configuration

Configuration is provided through the `.env` file and command-line arguments. The `--config` argument loads
additional configuration from a YAML or JSON file.

### Why so many configuration sources?

- The `.env` file contains secrets and service configuration that may need to change as part of the deployment
  - This includes the Discord bot token and the Comfy and Ollama server URLs
- The command line arguments contain runtime configuration that may change with each run
  - This includes the world save file and world prompt
- The `--config` file contains configuration that is too verbose or complex for the other two
  - This includes the checkpoints and sizes to be used for image generation

## Engine Notes

- The system is largely event-driven
- Each server or bot has its own thread (for error handling)
- Remote players can be implemented with any client, since they use a queue

## FAQ

1. Why are the `generate` and `simulate` functions not async?
   - Because I had written them before I realized they should be
2. Why is the web client in Typescript and React?
   - Because I have a template for that and it was easy to set up
3. Why does the web client use MUI?
   - Same as #2, it was easy to set up and use
4. Will the messages by localized?
   - Localization is a planned feature, but planned features should not be included in the readme

## TODOs

- figure out the human input syntax for actions
- make an admin panel in web UI
- store long-term memory for actors in a vector DB (RAG and all that)
- generate and simulate should probably be async
