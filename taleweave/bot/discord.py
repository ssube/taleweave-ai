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
    get_game_config,
    set_character_agent,
    subscribe,
)
from taleweave.models.config import DiscordBotConfig
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
    list_players,
    remove_player,
    set_player,
)
from taleweave.render.comfy import render_event
from taleweave.utils.search import list_characters
from taleweave.utils.template import format_prompt

logger = getLogger(__name__)
client = None

active_tasks = set()
event_messages: Dict[int, str | GameEvent] = {}
event_queue: Queue[GameEvent] = Queue()
player_mentions: Dict[str, str] = {}


def remove_tags(text: str) -> str:
    """
    Remove any <foo> tags.
    """

    return sub(r"<[^>]*>", "", text).strip()


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
                await reaction.message.add_reaction("❌")
                return

            event = event_messages[message_id]
            if isinstance(event, GameEvent):
                render_event(event)
                await reaction.message.add_reaction("📸")

    async def on_message(self, message):
        if message.author == self.user:
            return

        # make sure the message was in a valid channel
        active_channels = get_active_channels()
        if message.channel not in active_channels:
            return

        # get message contents
        config = get_game_config()
        author = message.author
        channel = message.channel
        user_name = author.name  # include nick
        content = remove_tags(message.content)

        if content.startswith(
            config.bot.discord.command_prefix + config.bot.discord.name_command
        ):
            world = get_current_world()
            if world:
                world_message = format_prompt(
                    "discord_world_active",
                    bot_name=config.bot.discord.name_title,
                    world=world,
                )
            else:
                world_message = format_prompt(
                    "discord_world_none", bot_name=config.bot.discord.name_title
                )

            await message.channel.send(world_message)
            return

        if content.startswith(config.bot.discord.command_prefix + "help"):
            await message.channel.send(
                format_prompt("discord_help", bot_name=config.bot.discord.name_command)
            )
            return

        if content.startswith(config.bot.discord.command_prefix + "join"):
            character_name = content.replace("!join", "").strip()
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
            player_mentions[user_name] = author.mention

            logger.info(f"{user_name} has joined the game as {character.name}!")
            join_event = PlayerEvent("join", character_name, user_name)
            return broadcast(join_event)

        if content.startswith(config.bot.discord.command_prefix + "characters"):
            world = get_current_world()
            if not world:
                await channel.send(
                    format_prompt(
                        "discord_characters_none",
                        bot_name=config.bot.discord.name_title,
                    )
                )
                return

            characters = [character.name for character in list_characters(world)]
            await channel.send(
                format_prompt(
                    "discord_characters_list",
                    bot_name=config.bot.discord.name_title,
                    characters=characters,
                )
            )
            return

        if content.startswith(config.bot.discord.command_prefix + "players"):
            players = list_players()
            await channel.send(embed=format_players(players))
            return

        player = get_player(user_name)
        if isinstance(player, RemotePlayer):
            if content.startswith(config.bot.discord.command_prefix + "leave"):
                remove_player(user_name)

                if user_name in player_mentions:
                    del player_mentions[user_name]

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
                player.input_queue.put(content)
                logger.info(
                    f"received message from {user_name} for {player.name}: {content}"
                )
                return

        await message.channel.send(format_prompt("discord_user_new"))
        return


def format_players(players: Dict[str, str]):
    player_embed = Embed(title="Players")
    for player, character in players.items():
        player_embed.add_field(name=player, value=character)

    return player_embed


def launch_bot(config: DiscordBotConfig):
    global client

    # message contents need to be enabled for multi-server bots
    intents = Intents.default()
    if config.content_intent:
        intents.message_content = True

    client = AdventureClient(intents=intents)

    def bot_main():
        if not client:
            raise ValueError("No Discord client available")

        client.run(environ["DISCORD_TOKEN"])

    def send_main():
        # from time import sleep

        while True:
            # sleep(0.05)
            # if event_queue.empty():
            # logger.debug("no events to prompt")
            #    continue

            # wait for pending messages to send, to keep them in order
            if len(active_tasks) > 0:
                # logger.debug("waiting for active tasks to complete")
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

    config = get_game_config()

    # return client.private_channels
    return [
        channel
        for guild in client.guilds
        for channel in guild.text_channels
        if channel.name in config.bot.discord.channels
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


def truncate(text: str, length: int = 1000) -> str:
    if len(text) > length:
        return text[:length] + "..."
    return text


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
    reply_embed.add_field(name="Reply", value=truncate(event.text))
    return reply_embed


def embed_from_generate(event: GenerateEvent) -> Embed:
    generate_embed = Embed(title="Generating", description=event.name)
    return generate_embed


def embed_from_result(event: ResultEvent):
    result_embed = Embed(title=event.room.name, description=event.character.name)
    result_embed.add_field(name="Result", value=truncate(event.result))
    return result_embed


def embed_from_player(event: PlayerEvent):
    if event.status == "join":
        title = format_prompt("discord_join_title", event=event)
        description = format_prompt("discord_join_result", event=event)
    else:
        title = format_prompt("discord_leave_title", event=event)
        description = format_prompt("discord_leave_result", event=event)

    player_embed = Embed(title=title, description=truncate(description))
    return player_embed


def embed_from_prompt(event: PromptEvent):
    prompt_embed = Embed(title=event.room.name, description=event.character.name)
    prompt_embed.add_field(name="Prompt", value=truncate(event.prompt))

    if has_player(event.character.name):
        players = list_players()
        user = next(
            (
                player
                for player, character in players.items()
                if character == event.character.name
            ),
            None,
        )

        if user:
            # use Discord user.mention to ping the user
            if user in player_mentions:
                user = player_mentions[user]

            prompt_embed.add_field(
                name="Player",
                value=user,
            )

    for action in event.actions:
        # TODO: use a prompt template to summarize actions
        action_name = action["function"]["name"]
        action_description = action["function"]["description"]
        prompt_embed.add_field(name=action_name, value=action_description)

    return prompt_embed


def embed_from_status(event: StatusEvent):
    status_embed = Embed(
        title=event.room.name if event.room else "",
        description=event.character.name if event.character else "",
    )
    status_embed.add_field(name="Status", value=truncate(event.text))
    return status_embed
