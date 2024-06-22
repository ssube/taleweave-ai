from functools import partial
from logging import getLogger
from typing import Any

from packit.agent import Agent
from packit.conditions import condition_or, condition_threshold
from packit.errors import ToolError
from packit.loops import loop_retry
from packit.results import function_result
from packit.toolbox import Toolbox

from taleweave.context import (
    get_action_group,
    get_character_agent_for_name,
    get_current_turn,
    get_game_config,
    get_prompt,
    set_current_character,
    set_current_room,
)
from taleweave.errors import ActionError
from taleweave.game_system import GameSystem
from taleweave.models.entity import Character, Room, World
from taleweave.utils.conversation import make_keyword_condition, summarize_room
from taleweave.utils.planning import (
    expire_events,
    get_recent_notes,
    get_upcoming_events,
)
from taleweave.utils.search import find_containing_room
from taleweave.utils.template import format_prompt

logger = getLogger(__name__)

PLANNING_SYSTEM_NAME = "planning"

# build a toolbox for the planners
planning_tools: Toolbox | None = None


def initialize_planning(world: World):
    global planning_tools

    planning_tools = Toolbox(get_action_group(PLANNING_SYSTEM_NAME))


def get_notes_events(character: Character, current_turn: int):
    recent_notes = get_recent_notes(character)
    upcoming_events = get_upcoming_events(character, current_turn)

    if len(recent_notes) > 0:
        notes = "\n".join(recent_notes)
        notes_prompt = format_prompt(
            "world_simulate_character_planning_notes_some", notes=notes
        )
    else:
        notes_prompt = format_prompt("world_simulate_character_planning_notes_none")

    if len(upcoming_events) > 0:
        current_turn = get_current_turn()
        events = [
            format_prompt(
                "world_simulate_character_planning_events_item",
                event=event,
                turns=event.turn - current_turn,
            )
            for event in upcoming_events
        ]
        events = "\n".join(events)
        events_prompt = format_prompt(
            "world_simulate_character_planning_events_some", events=events
        )
    else:
        events_prompt = format_prompt("world_simulate_character_planning_events_none")

    return notes_prompt, events_prompt


def prompt_character_planning(
    room: Room,
    character: Character,
    agent: Agent,
    toolbox: Toolbox,
    current_turn: int,
    max_steps: int | None = None,
) -> str:
    config = get_game_config()
    max_steps = max_steps or config.world.turn.planning_steps

    notes_prompt, events_prompt = get_notes_events(character, current_turn)

    event_count = len(character.planner.calendar.events)
    note_count = len(character.planner.notes)

    def result_parser(value, **kwargs):
        try:
            return function_result(value, **kwargs)
        except ToolError as e:
            e_str = str(e)
            if e_str and "Error running tool" in e_str:
                # extract the tool name and rest of the message from the error
                # the format is: "Error running tool: <action_name>: <message>"
                action_name, message = e_str.split(":", 2)
                action_name = action_name.removeprefix("Error running tool").strip()
                message = message.strip()
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_planning_error_action",
                        action=action_name,
                        message=message,
                    )
                )
            elif e_str and "Unknown tool" in e_str:
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_planning_error_unknown_tool",
                        actions=toolbox.list_tools(),
                    )
                )
            else:
                raise ActionError(
                    format_prompt(
                        "world_simulate_character_planning_error_json",
                        actions=toolbox.list_tools(),
                    )
                )

    logger.info("starting planning for character: %s", character.name)
    _, condition_end, result_parser = make_keyword_condition(
        get_prompt("world_simulate_character_planning_done"),
        result_parser=result_parser,
    )
    stop_condition = condition_or(
        condition_end, partial(condition_threshold, max=max_steps)
    )

    i = 0
    while not stop_condition(current=i):
        result = loop_retry(
            agent,
            format_prompt(
                "world_simulate_character_planning",
                event_count=event_count,
                events_prompt=events_prompt,
                note_count=note_count,
                notes_prompt=notes_prompt,
                room_summary=summarize_room(room, character),
            ),
            result_parser=result_parser,
            stop_condition=stop_condition,
            toolbox=toolbox,
        )

        if agent.memory:
            agent.memory.append(result)

        i += 1

    return result


def simulate_planning(world: World, turn: int, data: Any | None = None):
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
        expire_events(character, turn)

        # give the character a chance to think and check their planner
        if agent.memory and len(agent.memory) > 0:
            try:
                thoughts = prompt_character_planning(
                    room, character, agent, planning_tools, turn
                )
                logger.debug(f"{character.name} thinks: {thoughts}")
            except Exception:
                logger.exception(
                    f"error during planning for character {character.name}"
                )


def init():
    # TODO: add format method that renders the recent notes and upcoming events
    return [
        GameSystem(
            "planning", initialize=initialize_planning, simulate=simulate_planning
        )
    ]
