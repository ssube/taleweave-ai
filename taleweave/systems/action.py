from json import loads
from logging import getLogger
from typing import Any

from packit.errors import ToolError
from packit.loops import loop_retry
from packit.results import function_result
from packit.toolbox import Toolbox

from taleweave.context import (
    broadcast,
    get_action_group,
    get_character_agent_for_name,
    get_character_for_agent,
    get_current_world,
    set_current_character,
    set_current_room,
)
from taleweave.errors import ActionError
from taleweave.game_system import GameSystem
from taleweave.models.entity import World
from taleweave.models.event import ActionEvent, ResultEvent
from taleweave.utils.effect import expire_effects
from taleweave.utils.search import find_containing_room
from taleweave.utils.template import format_prompt
from taleweave.utils.world import format_attributes

from .planning import get_notes_events

ACTION_SYSTEM_NAME = "action"

logger = getLogger(__name__)


def world_result_parser(value, agent, **kwargs):
    current_world = get_current_world()
    if not current_world:
        raise ValueError(
            "The current world must be set before calling world_result_parser"
        )

    logger.debug(f"parsing action for {agent.name}: {value}")

    current_character = get_character_for_agent(agent)
    current_room = next(
        (room for room in current_world.rooms if current_character in room.characters),
        None,
    )

    set_current_room(current_room)
    set_current_character(current_character)

    return function_result(value, agent=agent, **kwargs)


def prompt_character_action(
    room, character, agent, action_toolbox, current_turn
) -> str:
    action_names = action_toolbox.list_tools()

    # collect data for the prompt
    notes_prompt, events_prompt = get_notes_events(character, current_turn)

    room_characters = [character.name for character in room.characters]
    room_items = [item.name for item in room.items]
    room_directions = [portal.name for portal in room.portals]

    character_attributes = format_attributes(character)
    # character_effects = [effect.name for effect in character.active_effects]
    character_items = [item.name for item in character.items]

    # set up a result parser for the agent
    def result_parser(value, **kwargs):
        if not room or not character:
            raise ValueError("Room and character must be set before parsing results")

        # trim suffixes that are used elsewhere
        value = value.removesuffix("END").strip()

        # fix the "action_ move" whitespace issue
        if '"action_ ' in value:
            value = value.replace('"action_ ', '"action_')

        # fix unbalanced curly braces
        if value.startswith("{") and not value.endswith("}"):
            open_count = value.count("{")
            close_count = value.count("}")

            if open_count > close_count:
                fixed_value = value + ("}" * (open_count - close_count))
                try:
                    loads(fixed_value)
                    value = fixed_value
                except Exception:
                    pass

        try:
            # TODO: try to avoid parsing the JSON twice
            event = ActionEvent.from_json(value, room, character)
            # TODO: decide if invalid actions should be broadcast
            broadcast(event)

            result = world_result_parser(value, **kwargs)

            return result
        except ToolError as e:
            e_str = str(e)
            if e_str and "Error running tool" in e_str:
                # extract the tool name and rest of the message from the error
                # the format is: "Error running tool: <action_name>: <message>"
                action_name, message = e_str.split(":", 1)
                action_name = action_name.removeprefix("Error running tool").strip()
                message = message.strip()
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_action_error_action",
                        action=action_name,
                        message=message,
                    )
                )
            elif e_str and "Unknown tool" in e_str:
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_action_error_unknown_tool",
                        actions=action_names,
                    )
                )
            else:
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_action_error_json",
                        actions=action_names,
                    )
                )

    # prompt and act
    logger.info("starting turn for character: %s", character.name)
    result = loop_retry(
        agent,
        format_prompt(
            "world_simulate_character_action",
            actions=action_names,
            character_items=character_items,
            attributes=character_attributes,
            directions=room_directions,
            room=room,
            visible_characters=room_characters,
            visible_items=room_items,
            notes_prompt=notes_prompt,
            events_prompt=events_prompt,
        ),
        result_parser=result_parser,
        toolbox=action_toolbox,
    )

    logger.debug(f"{character.name} action result: {result}")
    if agent.memory:
        agent.memory.append(result)

    return result


action_tools: Toolbox | None = None


def initialize_action(world: World):
    global action_tools

    action_tools = Toolbox(get_action_group(ACTION_SYSTEM_NAME))


def simulate_action(world: World, turn: int, data: Any | None = None):
    for character_name in world.order:
        character, agent = get_character_agent_for_name(character_name)
        if not agent or not character:
            logger.error(f"agent or character not found for name {character_name}")
            continue

        room = find_containing_room(world, character)
        if not room:
            logger.error(f"character {character_name} is not in a room")
            continue

        # prep context
        set_current_room(room)
        set_current_character(character)

        # decrement effects on the character and remove any that have expired
        expire_effects(character)

        try:
            result = prompt_character_action(room, character, agent, action_tools, turn)
            result_event = ResultEvent(result=result, room=room, character=character)
            broadcast(result_event)
        except Exception:
            logger.exception(f"error during action for character {character.name}")


def init_action():
    return [
        GameSystem(
            ACTION_SYSTEM_NAME, initialize=initialize_action, simulate=simulate_action
        )
    ]
