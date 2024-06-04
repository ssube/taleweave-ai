# Player's Guide to TaleWeave AI

## Contents

- [Player's Guide to TaleWeave AI](#players-guide-to-taleweave-ai)
  - [Contents](#contents)
  - [Playing in Discord](#playing-in-discord)
    - [Discord command syntax](#discord-command-syntax)
    - [Rendering events in Discord](#rendering-events-in-discord)
  - [Prompt syntax](#prompt-syntax)
    - [Prompt action syntax](#prompt-action-syntax)

## Playing in Discord

### Discord command syntax

*Note 1:* Because TaleWeave AI offers a dynamic set of actions depending on the game world, it does not currently use
Discord's command feature. If you know a way to make this work with constantly-changing actions, please let me know.

*Note 2:* When interacting with the Discord bot, you need to ping it with each message. Your server admin can allow the
bot to see all messages, with and without pings, but you must ping the bot by default.

The Discord bot offers the following commands:

- `!taleweave` or the bot name, if your admin changed it
  - prints the name of the active world
- `!help`
  - prints the available commands and their parameters
- `!join <character>`
  - join the game as the specified character
- `!leave`
  - leave the game, if you are playing
- `!characters`
  - list the available characters in the game
- `!players`
  - list the players currently in the game

Other messages will be treated as in-character input and used as your character's action or reply, depending on the
current prompt.

### Rendering events in Discord

You can render recent events in Discord by reacting to them with the camera emoji: 📷

If the bot can render that event, it will acknowledge your request with the camera flash emoji: 📸

When the images are ready, they will be posted to Discord as a reply to the event message.

## Prompt syntax

The web client displays a menu with all of the available actions on your turn, but you can also input your own actions
through text.

### Prompt action syntax

In order to call functions or use actions from your prompt replies, you (or more likely your GUI) can send valid JSON,
or you can use this prompt function syntax. Discord and the web client both support this syntax.

To use the prompt function syntax, start your prompt with `~` and use the syntax `~action:parameter=value,next=value`
where `action` is the name of the action (the function being called) and the remainder are parameters to be passed into
the function.

For example:

```none
~action_move:direction=north
~action_tell:character=Alice,message=Hello
~action_use:item=potion
```

There are some limits on this syntax:

- the function name cannot contain `:`
  - this is true in Python as well and should not be a problem
- the parameter names cannot contain `=`
  - this is also true in Python and should not be a problem
- the values cannot contain `,`
  - this is a problem and support for quotes is needed
