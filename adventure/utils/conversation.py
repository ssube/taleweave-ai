from functools import partial
from json import loads
from logging import getLogger
from typing import List

from packit.agent import Agent
from packit.conditions import condition_and, condition_threshold, make_flag_condition
from packit.results import multi_function_or_str_result
from packit.utils import could_be_json

from adventure.context import broadcast
from adventure.models.config import DEFAULT_CONFIG
from adventure.models.entity import Actor, Room

from .string import normalize_name

logger = getLogger(__name__)


actor_config = DEFAULT_CONFIG.world.actor


def make_keyword_condition(end_message: str, keywords=["end", "stop"]):
    set_end, condition_end = make_flag_condition()

    def result_parser(value, **kwargs):
        normalized_value = normalize_name(value)
        if normalized_value in keywords:
            logger.debug(f"found keyword, setting stop condition: {normalized_value}")
            set_end()
            return end_message

        # sometimes the models will make up a tool named after the keyword
        keyword_functions = [f'"function": "{kw}"' for kw in keywords]
        if could_be_json(normalized_value) and any(
            kw in normalized_value for kw in keyword_functions
        ):
            logger.debug(
                f"found keyword function, setting stop condition: {normalized_value}"
            )
            set_end()
            return end_message

        return multi_function_or_str_result(value, **kwargs)

    return set_end, condition_end, result_parser


def and_list(items: List[str]) -> str:
    """
    Convert a list of items into a human-readable list.
    """
    if not items:
        return "nothing"

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def or_list(items: List[str]) -> str:
    """
    Convert a list of items into a human-readable list.
    """
    if not items:
        return "nothing"

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])}, or {items[-1]}"


def summarize_room(room: Room, player: Actor) -> str:
    """
    Summarize a room for the player.
    """

    actor_names = and_list(
        [actor.name for actor in room.actors if actor.name != player.name]
    )
    item_names = and_list([item.name for item in room.items])
    inventory_names = and_list([item.name for item in player.items])

    return (
        f"You are in the {room.name} room with {actor_names}. "
        f"You see the {item_names} around the room. "
        f"You are carrying the {inventory_names}."
    )


def loop_conversation(
    room: Room,
    actors: List[Actor],
    agents: List[Agent],
    first_actor: Actor,
    first_prompt: str,
    reply_prompt: str,
    first_message: str,
    end_message: str,
    echo_function: str | None = None,
    echo_parameter: str | None = None,
    max_length: int | None = None,
) -> str | None:
    """
    Loop through a conversation between a series of agents, using metadata from their actors.
    """

    if max_length is None:
        max_length = actor_config.conversation_limit

    if len(actors) != len(agents):
        raise ValueError("The number of actors and agents must match.")

    _, condition_end, parse_end = make_keyword_condition(end_message)
    stop_length = partial(condition_threshold, max=max_length)
    stop_condition = condition_and(condition_end, stop_length)

    def result_parser(value: str, **kwargs) -> str:
        value = parse_end(value, **kwargs)

        if condition_end():
            return value

        if echo_function and could_be_json(value) and echo_function in value:
            value = loads(value).get("parameters", {}).get(echo_parameter, "")

        return value.strip()

    i = 0
    last_actor = first_actor
    response = first_message

    while not stop_condition(current=i):
        if i == 0:
            logger.debug(f"starting conversation with {first_actor.name}")
            prompt = first_prompt
        else:
            logger.debug(f"continuing conversation with {last_actor.name} on step {i}")
            prompt = reply_prompt

        # loop through the actors and agents
        actor = actors[i % len(actors)]
        agent = agents[i % len(agents)]

        # summarize the room and present the last response
        summary = summarize_room(room, actor)
        response = agent(
            prompt, response=response, summary=summary, last_actor=last_actor
        )
        response = result_parser(response)
        broadcast(f"{actor.name} responds: {response}")

        # increment the step counter
        i += 1
        last_actor = actor

    return response
