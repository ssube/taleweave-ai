from functools import partial
from json import loads
from logging import getLogger
from typing import List

from packit.agent import Agent
from packit.conditions import condition_or, condition_threshold, make_flag_condition
from packit.results import multi_function_or_str_result
from packit.utils import could_be_json

from adventure.context import broadcast
from adventure.models.config import DEFAULT_CONFIG
from adventure.models.entity import Character, Room
from adventure.models.event import ReplyEvent

from .string import and_list, normalize_name

logger = getLogger(__name__)


character_config = DEFAULT_CONFIG.world.character


def make_keyword_condition(end_message: str, keywords=["end", "stop"]):
    set_end, condition_end = make_flag_condition()

    def result_parser(value, **kwargs):
        normalized_value = normalize_name(value)
        if normalized_value in keywords:
            logger.debug(f"found keyword, setting stop condition: {normalized_value}")
            set_end()
            return end_message

        for keyword in keywords:
            if keyword == normalized_value:
                logger.debug(
                    f"found keyword, setting stop condition: {normalized_value}"
                )
                set_end()
                return end_message

            if normalized_value.endswith(keyword):
                logger.debug(
                    f"found keyword at end of string, setting stop condition: {normalized_value}"
                )
                set_end()
                return value[: -len(keyword)].strip()

            keyword_function = f'"function": "{keyword}"'
            if could_be_json(normalized_value) and keyword_function in normalized_value:
                logger.debug(
                    f"found keyword function, setting stop condition: {normalized_value}"
                )
                set_end()
                return end_message

        return multi_function_or_str_result(value, **kwargs)

    return set_end, condition_end, result_parser


def summarize_room(room: Room, player: Character) -> str:
    """
    Summarize a room for the player.
    """

    character_names = and_list(
        [
            character.name
            for character in room.characters
            if character.name != player.name
        ]
    )
    item_names = and_list([item.name for item in room.items])
    inventory_names = and_list([item.name for item in player.items])

    return (
        f"You are in the {room.name} room with {character_names}. "
        f"You see the {item_names} around the room. "
        f"You are carrying the {inventory_names}."
    )


def loop_conversation(
    room: Room,
    characters: List[Character],
    agents: List[Agent],
    first_character: Character,
    first_prompt: str,
    reply_prompt: str,
    first_message: str,
    end_message: str,
    echo_function: str | None = None,
    echo_parameter: str | None = None,
    max_length: int | None = None,
) -> str | None:
    """
    Loop through a conversation between a series of agents, using metadata from their characters.
    """

    if max_length is None:
        max_length = character_config.conversation_limit

    if len(characters) != len(agents):
        raise ValueError("The number of characters and agents must match.")

    # set up the keyword or length-limit compound condition
    _, condition_end, parse_end = make_keyword_condition(end_message)
    stop_length = partial(condition_threshold, max=max_length)
    stop_condition = condition_or(condition_end, stop_length)

    # prepare a result parser looking for the echo function
    def result_parser(value: str, **kwargs) -> str:
        value = parse_end(value, **kwargs)

        if condition_end():
            return value

        if echo_function and could_be_json(value) and echo_function in value:
            value = loads(value).get("parameters", {}).get(echo_parameter, "")

        return value.strip()

    # prepare the loop state
    i = 0
    last_character = first_character
    response = first_message

    while not stop_condition(current=i):
        if i == 0:
            logger.debug(f"starting conversation with {first_character.name}")
            prompt = first_prompt
        else:
            logger.debug(
                f"continuing conversation with {last_character.name} on step {i}"
            )
            prompt = reply_prompt

        # loop through the characters and agents
        character = characters[i % len(characters)]
        agent = agents[i % len(agents)]

        # summarize the room and present the last response
        summary = summarize_room(room, character)
        response = agent(
            prompt, response=response, summary=summary, last_character=last_character
        )
        response = result_parser(response)

        logger.info(f"{character.name} responds: {response}")
        reply_event = ReplyEvent.from_text(response, room, character)
        broadcast(reply_event)

        # increment the step counter
        i += 1
        last_character = character

    return response
