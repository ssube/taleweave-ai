from logging import getLogger
from os import environ
from queue import Queue
from re import sub
from threading import Thread
from typing import Tuple

from discord import Client, Embed, File, Intents

from adventure.context import (
    get_actor_agent_for_name,
    get_current_world,
    set_actor_agent,
)
from adventure.models.event import (
    ActionEvent,
    GameEvent,
    GenerateEvent,
    PromptEvent,
    ReplyEvent,
    ResultEvent,
    StatusEvent,
)
from adventure.player import RemotePlayer, get_player, has_player, set_player
from adventure.render_comfy import generate_image_tool

logger = getLogger(__name__)
client = None

active_tasks = set()
prompt_queue: Queue[Tuple[GameEvent, Embed | str]] = Queue()


def remove_tags(text: str) -> str:
    """
    Remove any <foo> tags.
    """

    return sub(r"<[^>]*>", "", text)


def find_embed_field(embed: Embed, name: str) -> str | None:
    return next((field.value for field in embed.fields if field.name == name), None)


# TODO: becomes prompt from event
def prompt_from_embed(embed: Embed) -> str | None:
    room_name = embed.title
    actor_name = embed.description

    world = get_current_world()
    if not world:
        return

    room = next((room for room in world.rooms if room.name == room_name), None)
    if not room:
        return

    actor = next((actor for actor in room.actors if actor.name == actor_name), None)
    if not actor:
        return

    item_field = find_embed_field(embed, "Item")

    action_field = find_embed_field(embed, "Action")
    if action_field:
        if item_field:
            item = next(
                (
                    item
                    for item in (room.items + actor.items)
                    if item.name == item_field
                ),
                None,
            )
            if item:
                return f"{actor.name} {action_field} the {item.name}. {item.description}. {actor.description}. {room.description}."

            return f"{actor.name} {action_field} the {item_field}. {actor.description}. {room.description}."

        return f"{actor.name} {action_field}. {actor.description}. {room.name}."

    result_field = find_embed_field(embed, "Result")
    if result_field:
        return f"{result_field}. {actor.description}. {room.description}."

    return


class AdventureClient(Client):
    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return

        logger.info(f"Reaction added: {reaction} by {user}")
        if reaction.emoji == "📷":
            # message_id = reaction.message.id
            # TODO: look up event that caused this message, get the room and actors
            if len(reaction.message.embeds) > 0:
                embed = reaction.message.embeds[0]
                prompt = prompt_from_embed(embed)
            else:
                prompt = remove_tags(reaction.message.content)
                if prompt.startswith("Generating"):
                    # TODO: get the entity from the message
                    pass

            await reaction.message.add_reaction("📸")
            paths = generate_image_tool(prompt, 2)
            logger.info(f"Generated images: {paths}")

            files = [File(filename) for filename in paths]
            await reaction.message.channel.send(files=files, reference=reaction.message)

    async def on_message(self, message):
        if message.author == self.user:
            return

        author = message.author
        channel = message.channel
        user_name = author.name  # include nick

        world = get_current_world()
        if world:
            active_world = f"Active world: {world.name} (theme: {world.theme})"
        else:
            active_world = "No active world"

        if message.content.startswith("!adventure"):
            await message.channel.send(f"Hello! Welcome to Adventure! {active_world}")
            return

        if message.content.startswith("!help"):
            await message.channel.send("Type `!join` to start playing!")
            return

        if message.content.startswith("!join"):
            character_name = remove_tags(message.content).replace("!join", "").strip()
            if has_player(character_name):
                await channel.send(f"{character_name} has already been taken!")
                return

            actor, agent = get_actor_agent_for_name(character_name)
            if not actor:
                await channel.send(f"Character `{character_name}` not found!")
                return

            def prompt_player(event: PromptEvent):
                logger.info(
                    "append prompt for character %s (user %s) to queue: %s",
                    event.actor.name,
                    user_name,
                    event.prompt,
                )

                # TODO: build an embed from the prompt
                prompt_queue.put((event, event.prompt))
                return True

            player = RemotePlayer(
                actor.name, actor.backstory, prompt_player, fallback_agent=agent
            )
            set_actor_agent(character_name, actor, player)
            set_player(user_name, player)

            logger.info(f"{user_name} has joined the game as {actor.name}!")
            await message.channel.send(
                f"{user_name} has joined the game as {actor.name}!"
            )
            return

        if message.content.startswith("!leave"):
            # TODO: revert to LLM agent
            logger.info(f"{user_name} has left the game!")
            await message.channel.send(f"{user_name} has left the game!")
            return

        player = get_player(user_name)
        if player and isinstance(player, RemotePlayer):
            content = remove_tags(message.content)
            player.input_queue.put(content)
            logger.info(
                f"Received message from {user_name} for {player.name}: {content}"
            )
            return

        await message.channel.send(
            "You are not currently playing Adventure! Type `!join` to start playing!"
        )
        return


def launch_bot():
    def bot_main():
        global client

        intents = Intents.default()
        # intents.message_content = True

        client = AdventureClient(intents=intents)
        client.run(environ["DISCORD_TOKEN"])

    def prompt_main():
        from time import sleep

        while True:
            sleep(0.1)
            if prompt_queue.empty():
                continue

            if len(active_tasks) > 0:
                continue

            event, prompt = prompt_queue.get()
            logger.info("Prompting for event %s: %s", event, prompt)

            if client:
                prompt_task = client.loop.create_task(broadcast_event(prompt))
                active_tasks.add(prompt_task)
                prompt_task.add_done_callback(active_tasks.discard)

    bot_thread = Thread(target=bot_main, daemon=True)
    bot_thread.start()

    prompt_thread = Thread(target=prompt_main, daemon=True)
    prompt_thread.start()

    return [bot_thread, prompt_thread]


def stop_bot():
    global client

    if client:
        client.close()
        client = None


# @cache
def get_active_channels():
    if not client:
        return []

    # return client.private_channels
    return [
        channel
        for guild in client.guilds
        for channel in guild.text_channels
        if channel.name == "bots"
    ]


async def broadcast_event(message: str | Embed):
    if not client:
        logger.warning("No Discord client available")
        return

    active_channels = get_active_channels()
    if not active_channels:
        logger.warning("No active channels")
        return

    for channel in active_channels:
        if isinstance(message, str):
            logger.info("Broadcasting to channel %s: %s", channel, message)
            await channel.send(content=message)
        elif isinstance(message, Embed):
            logger.info(
                "Broadcasting to channel %s: %s - %s",
                channel,
                message.title,
                message.description,
            )
            await channel.send(embed=message)


def bot_event(event: GameEvent):
    if isinstance(event, GenerateEvent):
        bot_generate(event)
    elif isinstance(event, ResultEvent):
        bot_result(event)
    elif isinstance(event, (ActionEvent, ReplyEvent)):
        bot_action(event)
    elif isinstance(event, StatusEvent):
        pass
    else:
        logger.warning("Unknown event type: %s", event)


def bot_action(event: ActionEvent | ReplyEvent):
    try:
        action_embed = Embed(title=event.room.name, description=event.actor.name)

        if isinstance(event, ActionEvent):
            action_name = event.action.replace("action_", "").title()
            action_parameters = event.parameters

            action_embed.add_field(name="Action", value=action_name)

            for key, value in action_parameters.items():
                action_embed.add_field(name=key.replace("_", " ").title(), value=value)
        else:
            action_embed.add_field(name="Message", value=event.text)

        prompt_queue.put((event, action_embed))
    except Exception as e:
        logger.error("Failed to broadcast action: %s", e)


def bot_generate(event: GenerateEvent):
    prompt_queue.put((event, event.name))


def bot_result(event: ResultEvent):
    text = event.result
    if len(text) > 1000:
        text = text[:1000] + "..."

    result_embed = Embed(title=event.room.name, description=event.actor.name)
    result_embed.add_field(name="Result", value=text)
    prompt_queue.put((event, result_embed))
