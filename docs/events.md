# TaleWeave AI Events

## Contents

- [TaleWeave AI Events](#taleweave-ai-events)
  - [Contents](#contents)
  - [Event Types](#event-types)
  - [Player Events](#player-events)
    - [Player Join Events](#player-join-events)
    - [Player Leave Events](#player-leave-events)
  - [System Events](#system-events)
    - [Generate Events](#generate-events)
  - [World Events](#world-events)
    - [Action Events](#action-events)
    - [Prompt Events](#prompt-events)
    - [Reply Events](#reply-events)
    - [Result Events](#result-events)
    - [Status Events](#status-events)
  - [Server-specific Events](#server-specific-events)
    - [Websocket Server Events](#websocket-server-events)
      - [Websocket New Client](#websocket-new-client)
      - [Websocket Player Become Character](#websocket-player-become-character)
      - [Websocket Player Input](#websocket-player-input)
      - [Websocket Player Name](#websocket-player-name)

## Event Types

- Player events
  - Joining
  - Leaving
- System events
  - Generating the world?
- World events
  - Things happening in the world

## Player Events

Player events use the following schema:

```yaml
event: "player"
status: string
character: string
client: string
```

### Player Join Events

Player join events have a `status` of `join`:

```yaml
event: "player"
status: "join"
character: string
client: string
```

### Player Leave Events

Player leave events have a `status` of `leave`:

```yaml
event: "player"
status: "leave"
character: string
client: string
```

## System Events

### Generate Events

Generate events are sent every time an entity's name is generated and again when it has been completely generated and
added to the world.

```yaml
event: "generate"
name: str
entity: Room | Actor | Item | None
```

Two `generate` events will be fired for each entity. The first event will *not* have an `entity` set, only the `name`.
The second event after generation is complete will have the same `name` and the full `entity`. This helps provide
more frequent progress updates when generating with slow models.

## World Events

### Action Events

### Prompt Events

### Reply Events

### Result Events

### Status Events

## Server-specific Events

### Websocket Server Events

The websocket server has a few unique message types that it uses to communicate metadata with socket clients.

#### Websocket New Client

Notify a new client of its unique ID.

```yaml
type: "id"
id: str
```

This is an outgoing event from the server to clients.

#### Websocket Player Become Character

A socket client wants to play as a character in the world.

```yaml
type: "player"
become: str
```

This is an incoming event from clients to the server.

#### Websocket Player Input

A socket client has sent some input, usually in response to a prompt.

```yaml
type: "input"
input: str
```

This is an incoming event from clients to the server.

#### Websocket Player Name

Update the player name attached to a socket client.

```yaml
type: "player"
name: str
```

This is an incoming event from clients to the server.
