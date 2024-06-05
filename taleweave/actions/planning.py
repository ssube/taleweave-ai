from taleweave.context import (
    action_context,
    get_agent_for_character,
    get_current_turn,
    get_game_config,
    get_prompt,
)
from taleweave.errors import ActionError
from taleweave.models.planning import CalendarEvent
from taleweave.utils.planning import get_recent_notes
from taleweave.utils.prompt import format_prompt


def take_note(fact: str):
    """
    Remember a fact by recording it in your notes. Facts are critical information about yourself and others that you
    have learned during your adventures. You can review your notes at any time to help you make decisions.

    Args:
        fact: The fact to remember.
    """

    config = get_game_config()

    with action_context() as (_, action_character):
        if fact in action_character.planner.notes:
            raise ActionError(get_prompt("action_take_note_error_duplicate"))

        if len(action_character.planner.notes) >= config.world.character.note_limit:
            raise ActionError(get_prompt("action_take_note_error_limit"))

        action_character.planner.notes.append(fact)

        return get_prompt("action_take_note_result")


def read_notes(unused: bool, count: int = 10):
    """
    Read your notes to review the facts that you have learned during your adventures.

    Args:
        count: The number of recent notes to read. 10 is usually a good number.
    """

    with action_context() as (_, action_character):
        facts = get_recent_notes(action_character, count=count)
        return "\n".join(facts)


def erase_notes(prefix: str) -> str:
    """
    Erase notes that start with a specific prefix.

    Args:
        prefix: The prefix to match notes against.
    """

    with action_context() as (_, action_character):
        if len(action_character.planner.notes) == 0:
            raise ActionError(get_prompt("action_erase_notes_error_empty"))

        matches = [
            note for note in action_character.planner.notes if note.startswith(prefix)
        ]
        if not matches:
            raise ActionError(get_prompt("action_erase_notes_error_match"))

        action_character.planner.notes[:] = [
            note for note in action_character.planner.notes if note not in matches
        ]

        return format_prompt("action_erase_notes_result", count=len(matches))


def edit_note(old: str, new: str) -> str:
    """
    Modify a note with new details.

    Args:
        old: The old note to replace.
        new: The new note to replace it with.
    """

    with action_context() as (_, action_character):
        if len(action_character.planner.notes) == 0:
            raise ActionError(get_prompt("action_edit_note_error_empty"))

        if old not in action_character.planner.notes:
            raise ActionError(get_prompt("action_edit_note_error_match"))

        action_character.planner.notes[:] = [
            new if note == old else note for note in action_character.planner.notes
        ]

        return get_prompt("action_edit_note_result")


def summarize_notes(limit: int) -> str:
    """
    Summarize your notes by combining similar notes and removing duplicates.

    Args:
        limit: The maximum number of notes to keep.
    """

    config = get_game_config()

    with action_context() as (_, action_character):
        notes = action_character.planner.notes
        if len(notes) == 0:
            raise ActionError(get_prompt("action_summarize_notes_error_empty"))

        action_agent = get_agent_for_character(action_character)

        if not action_agent:
            raise ActionError("Agent missing for character {action_character.name}")

        summary = action_agent(
            get_prompt("action_summarize_notes_prompt"),
            limit=limit,
            notes=notes,
        )

        new_notes = [note.strip() for note in summary.split("\n") if note.strip()]
        if len(new_notes) > config.world.character.note_limit:
            raise ActionError(
                format_prompt(
                    "action_summarize_notes_error_limit",
                    limit=config.world.character.note_limit,
                )
            )

        action_character.planner.notes[:] = new_notes
        return get_prompt("action_summarize_notes_result")


def schedule_event(name: str, turns: int):
    """
    Schedule an event to happen at a specific turn. Events are important occurrences that can affect the world in
    significant ways. You will be notified about upcoming events so you can plan accordingly. Make sure you inform
    other characters about events that involve them, and give them enough time to prepare.

    Args:
        name: The name of the event.
        turns: The number of turns until the event happens.
    """

    config = get_game_config()
    current_turn = get_current_turn()

    with action_context() as (_, action_character):
        if not name:
            raise ActionError(get_prompt("action_schedule_event_error_name"))

        if (
            len(action_character.planner.calendar.events)
            >= config.world.character.event_limit
        ):
            raise ActionError(get_prompt("action_schedule_event_error_limit"))

        if name in [event.name for event in action_character.planner.calendar.events]:
            raise ActionError(get_prompt("action_schedule_event_error_duplicate"))

        event = CalendarEvent(name, turns + current_turn)
        action_character.planner.calendar.events.append(event)
        return format_prompt("action_schedule_event_result", name=name, turns=turns)


def check_calendar(count: int):
    """
    Read your calendar to see upcoming events that you have scheduled.

    Args:
        count: The number of upcoming events to read. 5 is usually a good number.
    """

    config = get_game_config()

    count = min(count, config.world.character.event_limit)
    current_turn = get_current_turn()

    with action_context() as (_, action_character):
        if len(action_character.planner.calendar.events) == 0:
            return get_prompt("action_check_calendar_empty")

        events = action_character.planner.calendar.events[:count]
        return "\n".join(
            [
                format_prompt(
                    "action_check_calendar_each",
                    name=event.name,
                    turns=event.turn - current_turn,
                )
                for event in events
            ]
        )
