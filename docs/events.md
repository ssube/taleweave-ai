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
    - [Snapshot Events](#snapshot-events)
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
type: "player"
status: string
character: string
client: string
```

### Player Join Events

Player join events have a `status` of `join`:

```yaml
type: "player"
status: "join"
character: string
client: string
```

### Player Leave Events

Player leave events have a `status` of `leave`:

```yaml
type: "player"
status: "leave"
character: string
client: string
```

## System Events

### Generate Events

Generate events are sent every time an entity's name is generated and again when it has been completely generated and
added to the world.

```yaml
type: "generate"
name: string
entity: Room | Actor | Item | None
```

Two `generate` events will be fired for each entity. The first event will *not* have an `entity` set, only the `name`.
The second event after generation is complete will have the same `name` and the full `entity`. This helps provide
more frequent progress updates when generating with slow models.

## World Events

### Action Events

The action event is fired after player or actor input has been processed and any JSON function calls have been parsed.

```yaml
type: "action"
action: string
parameters: dict
room: Room
actor: Actor
item: Item | None
```

### Prompt Events

The prompt event is fired when a character's turn starts and their input is needed for the next action.

```yaml
type: "prompt"
prompt: string
room: Room
actor: Actor
```

### Reply Events

The reply event is fired when a character has been asked a question or told a message and replies.

```yaml
type: "reply"
text: string
room: Room
actor: Actor
```

### Result Events

The result event is fired after a character has taken an action and contains the results of that action.

```yaml
type: "result"
result: string
room: Room
actor: Actor
```

The result is related to the most recent action for the same actor, although not every action will have a result - they
may have a reply or error instead.

### Status Events

The status event is fired for general events in the world and messages about other characters.

```yaml
type: "status"
text: string
room: Room | None
actor: Actor | None
```

### Snapshot Events

The snapshot event is fired at the end of each turn and contains a complete snapshot of the world.

```yaml
type: "snapshot"
world: Dict
memory: Dict
step: int
```

This is primarily used to save the world state, but can also be used to sync clients and populate the world menu.

The `world` and `memory` fields within the snapshot event have already been serialized to JSON-compatible dictionaries,
because they may contain complex classes and implementation details of the underlying LLM.

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
