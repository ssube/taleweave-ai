from logging import getLogger
from os import environ
from queue import Queue
from re import sub
from threading import Thread
from typing import Dict

from discord import Client, Embed, File, Intents

from taleweave.context import (
    broadcast,
    get_character_agent_for_name,
    get_current_world,
    set_character_agent,
    subscribe,
)
from taleweave.models.config import DEFAULT_CONFIG, DiscordBotConfig
from taleweave.models.event import (
    ActionEvent,
    GameEvent,
    GenerateEvent,
    PlayerEvent,
    PromptEvent,
    RenderEvent,
    ReplyEvent,
    ResultEvent,
    StatusEvent,
)
from taleweave.player import (
    RemotePlayer,
    get_player,
    has_player,
    remove_player,
    set_player,
)
from taleweave.render.comfy import render_event
from taleweave.utils.prompt import format_prompt

logger = getLogger(__name__)
client = None
bot_config: DiscordBotConfig = DEFAULT_CONFIG.bot.discord

active_tasks = set()
event_messages: Dict[int, str | GameEvent] = {}
event_queue: Queue[GameEvent] = Queue()


def remove_tags(text: str) -> str:
    """
    Remove any <foo> tags.
    """

    return sub(r"<[^>]*>", "", text)


class AdventureClient(Client):
    async def on_ready(self):
        logger.info(f"logged in as {self.user}")

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return

        logger.info(f"reaction added: {reaction} by {user}")
        if reaction.emoji == "📷":
            message_id = reaction.message.id
            if message_id not in event_messages:
                logger.warning(f"message {message_id} not found in event messages")
                # TODO: return error message
                return

            event = event_messages[message_id]
            if isinstance(event, GameEvent):
                render_event(event)
                await reaction.message.add_reaction("📸")

    async def on_message(self, message):
        if message.author == self.user:
            return

        author = message.author
        channel = message.channel
        user_name = author.name  # include nick

        if message.content.startswith(
            bot_config.command_prefix + bot_config.name_command
        ):
            world = get_current_world()
            if world:
                world_message = format_prompt(
                    "discord_world_active", bot_name=bot_config.name_title, world=world
                )
            else:
                world_message = format_prompt(
                    "discord_world_none", bot_name=bot_config.name_title
                )

            await message.channel.send(world_message)
            return

        if message.content.startswith("!help"):
            await message.channel.send(
                format_prompt("discord_help", bot_name=bot_config.name_command)
            )
            return

        if message.content.startswith("!join"):
            character_name = remove_tags(message.content).replace("!join", "").strip()
            if has_player(character_name):
                await channel.send(
                    format_prompt("discord_join_error_taken", character=character_name)
                )
                return

            character, agent = get_character_agent_for_name(character_name)
            if not character:
                await channel.send(
                    format_prompt(
                        "discord_join_error_not_found", character=character_name
                    )
                )
                return

            def prompt_player(event: PromptEvent):
                logger.info(
                    "append prompt for character %s (user %s) to queue: %s",
                    event.character.name,
                    user_name,
                    event.prompt,
                )

                event_queue.put(event)
                return True

            player = RemotePlayer(
                character.name, character.backstory, prompt_player, fallback_agent=agent
            )
            set_character_agent(character_name, character, player)
            set_player(user_name, player)

            logger.info(f"{user_name} has joined the game as {character.name}!")
            join_event = PlayerEvent("join", character_name, user_name)
            return broadcast(join_event)

        player = get_player(user_name)
        if isinstance(player, RemotePlayer):
            if message.content.startswith("!leave"):
                remove_player(user_name)

                # revert to LLM agent
                character, _ = get_character_agent_for_name(player.name)
                if character and player.fallback_agent:
                    logger.info("restoring LLM agent for %s", player.name)
                    set_character_agent(
                        character.name, character, player.fallback_agent
                    )

                # broadcast leave event
                logger.info("disconnecting player %s from %s", user_name, player.name)
                leave_event = PlayerEvent("leave", player.name, user_name)
                return broadcast(leave_event)
            else:
                content = remove_tags(message.content)
                player.input_queue.put(content)
                logger.info(
                    f"received message from {user_name} for {player.name}: {content}"
                )
                return

        await message.channel.send(format_prompt("discord_user_new"))
        return


def launch_bot(config: DiscordBotConfig):
    global bot_config
    global client

    bot_config = config

    # message contents need to be enabled for multi-server bots
    intents = Intents.default()
    if bot_config.content_intent:
        intents.message_content = True

    client = AdventureClient(intents=intents)

    def bot_main():
        if not client:
            raise ValueError("No Discord client available")

        client.run(environ["DISCORD_TOKEN"])

    def send_main():
        from time import sleep

        while True:
            sleep(0.1)
            if event_queue.empty():
                # logger.debug("no events to prompt")
                continue

            # wait for pending messages to send, to keep them in order
            if len(active_tasks) > 0:
                logger.debug("waiting for active tasks to complete")
                continue

            event = event_queue.get()
            logger.debug("broadcasting %s event", event.type)

            if client:
                event_task = client.loop.create_task(broadcast_event(event))
                active_tasks.add(event_task)
                event_task.add_done_callback(active_tasks.discard)
            else:
                logger.warning("no Discord client available")

    logger.info("launching Discord bot")
    bot_thread = Thread(target=bot_main, daemon=True)
    bot_thread.start()

    send_thread = Thread(target=send_main, daemon=True)
    send_thread.start()

    subscribe(GameEvent, bot_event)

    return [bot_thread, send_thread]


def stop_bot():
    global client

    if client:
        close_task = client.loop.create_task(client.close())
        active_tasks.add(close_task)

        def on_close_task_done(future):
            logger.info("discord client closed")
            active_tasks.discard(future)

        close_task.add_done_callback(on_close_task_done)
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
        if channel.name in bot_config.channels
    ]


def bot_event(event: GameEvent):
    event_queue.put(event)


async def broadcast_event(message: str | GameEvent):
    if not client:
        logger.warning("no Discord client available")
        return

    active_channels = get_active_channels()
    if not active_channels:
        logger.warning("no active channels")
        return

    for channel in active_channels:
        if isinstance(message, str):
            # deprecated, use events instead
            logger.warning(
                "broadcasting non-event message to channel %s: %s", channel, message
            )
            event_message = await channel.send(content=message)
        elif isinstance(message, RenderEvent):
            # special handling to upload images
            # find the source event
            source_event_id = message.source.id
            source_message_id = next(
                (
                    message_id
                    for message_id, event in event_messages.items()
                    if isinstance(event, GameEvent) and event.id == source_event_id
                ),
                None,
            )
            if not source_message_id:
                logger.warning("source event not found: %s", source_event_id)
                return

            # open and upload images
            files = [File(filename) for filename in message.paths]
            try:
                source_message = await channel.fetch_message(source_message_id)
            except Exception as err:
                logger.warning("source message not found: %s", err)
                return

            # send the images as a reply to the source message
            event_message = await source_message.channel.send(
                files=files, reference=source_message
            )
        else:
            embed = embed_from_event(message)
            if not embed:
                logger.warning("no embed for event: %s", message)
                return

            logger.info(
                "broadcasting to channel %s: %s - %s",
                channel,
                embed.title,
                embed.description,
            )
            event_message = await channel.send(embed=embed)

        event_messages[event_message.id] = message


def embed_from_event(event: GameEvent) -> Embed | None:
    if isinstance(event, GenerateEvent):
        return embed_from_generate(event)
    elif isinstance(event, ResultEvent):
        return embed_from_result(event)
    elif isinstance(event, ActionEvent):
        return embed_from_action(event)
    elif isinstance(event, ReplyEvent):
        return embed_from_reply(event)
    elif isinstance(event, StatusEvent):
        return embed_from_status(event)
    elif isinstance(event, PlayerEvent):
        return embed_from_player(event)
    elif isinstance(event, PromptEvent):
        return embed_from_prompt(event)
    else:
        logger.warning("unknown event type: %s", event)


def embed_from_action(event: ActionEvent):
    action_embed = Embed(title=event.room.name, description=event.character.name)
    action_name = event.action.replace("action_", "").title()
    action_parameters = event.parameters

    action_embed.add_field(name="Action", value=action_name)

    for key, value in action_parameters.items():
        action_embed.add_field(name=key.replace("_", " ").title(), value=value)

    return action_embed


def embed_from_reply(event: ReplyEvent):
    reply_embed = Embed(title=event.room.name, description=event.speaker.name)
    reply_embed.add_field(name="Reply", value=event.text)
    return reply_embed


def embed_from_generate(event: GenerateEvent) -> Embed:
    generate_embed = Embed(title="Generating", description=event.name)
    return generate_embed


def embed_from_result(event: ResultEvent):
    text = event.result
    if len(text) > 1000:
        text = text[:1000] + "..."

    result_embed = Embed(title=event.room.name, description=event.character.name)
    result_embed.add_field(name="Result", value=text)
    return result_embed


def embed_from_player(event: PlayerEvent):
    if event.status == "join":
        title = format_prompt("discord_join_title", event=event)
        description = format_prompt("discord_join_result", event=event)
    else:
        title = format_prompt("discord_leave_title", event=event)
        description = format_prompt("discord_leave_result", event=event)

    player_embed = Embed(title=title, description=description)
    return player_embed


def embed_from_prompt(event: PromptEvent):
    # TODO: ping the player
    prompt_embed = Embed(title=event.room.name, description=event.character.name)
    prompt_embed.add_field(name="Prompt", value=event.prompt)
    return prompt_embed


def embed_from_status(event: StatusEvent):
    status_embed = Embed(
        title=event.room.name if event.room else "",
        description=event.character.name if event.character else "",
    )
    status_embed.add_field(name="Status", value=event.text)
    return status_embed
