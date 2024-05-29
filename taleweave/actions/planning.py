from taleweave.context import action_context, get_agent_for_character, get_current_turn
from taleweave.errors import ActionError
from taleweave.models.config import DEFAULT_CONFIG
from taleweave.models.planning import CalendarEvent
from taleweave.utils.planning import get_recent_notes

character_config = DEFAULT_CONFIG.world.character


def take_note(fact: str):
    """
    Remember a fact by recording it in your notes. Facts are critical information about yourself and others that you
    have learned during your adventures. You can review your notes at any time to help you make decisions.

    Args:
        fact: The fact to remember.
    """

    with action_context() as (_, action_character):
        if fact in action_character.planner.notes:
            raise ActionError(
                "You already have a note about that fact. You do not need to take duplicate notes. "
                "If you have too many notes, consider erasing, replacing, or summarizing them."
            )

        if len(action_character.planner.notes) >= character_config.note_limit:
            raise ActionError(
                "You have reached the limit of notes you can take. Please erase, replace, or summarize some notes."
            )

        action_character.planner.notes.append(fact)

        return "You make a note of that fact."


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
        matches = [
            note for note in action_character.planner.notes if note.startswith(prefix)
        ]
        if not matches:
            return "No notes found with that prefix."

        action_character.planner.notes[:] = [
            note for note in action_character.planner.notes if note not in matches
        ]
        return f"Erased {len(matches)} notes."


def replace_note(old: str, new: str) -> str:
    """
    Replace a note with a new note.

    Args:
        old: The old note to replace.
        new: The new note to replace it with.
    """

    with action_context() as (_, action_character):
        if old not in action_character.planner.notes:
            return "Note not found."

        action_character.planner.notes[:] = [
            new if note == old else note for note in action_character.planner.notes
        ]
        return "Note replaced."


def summarize_notes(limit: int) -> str:
    """
    Summarize your notes by combining similar notes and removing duplicates.

    Args:
        limit: The maximum number of notes to keep.
    """

    with action_context() as (_, action_character):
        notes = action_character.planner.notes
        action_agent = get_agent_for_character(action_character)

        if not action_agent:
            raise ActionError("Agent missing for character {action_character.name}")

        summary = action_agent(
            "Please summarize your notes. Remove any duplicates and combine similar notes. "
            "If a newer note contradicts an older note, keep the newer note. "
            "Clean up your notes so you can focus on the most important facts. "
            "Respond with one note per line. You can have up to {limit} notes, "
            "so make sure you reply with less than {limit} lines. Do not number the lines "
            "in your response. Do not include any JSON or other information. "
            "Your notes are:\n{notes}",
            limit=limit,
            notes=notes,
        )

        new_notes = [note.strip() for note in summary.split("\n") if note.strip()]
        if len(new_notes) > character_config.note_limit:
            raise ActionError(
                f"Too many notes. You can only have up to {character_config.note_limit} notes."
            )

        action_character.planner.notes[:] = new_notes
        return "Notes were summarized successfully."


def schedule_event(name: str, turns: int):
    """
    Schedule an event to happen at a specific turn. Events are important occurrences that can affect the world in
    significant ways. You will be notified about upcoming events so you can plan accordingly. Make sure you inform
    other characters about events that involve them, and give them enough time to prepare.

    Args:
        name: The name of the event.
        turns: The number of turns until the event happens.
    """

    # TODO: check for existing events with the same name
    # TODO: limit the number of events that can be scheduled

    with action_context() as (_, action_character):
        event = CalendarEvent(name, turns)
        action_character.planner.calendar.events.append(event)
        return f"{name} is scheduled to happen in {turns} turns."


def check_calendar(count: int):
    """
    Read your calendar to see upcoming events that you have scheduled.

    Args:
        count: The number of upcoming events to read. 5 is usually a good number.
    """

    count = min(count, character_config.event_limit)
    current_turn = get_current_turn()

    with action_context() as (_, action_character):
        if len(action_character.planner.calendar.events) == 0:
            return (
                "You have no upcoming events scheduled. You can plan events with other characters or on your own. "
                "Make sure to inform others about events that involve them."
            )

        events = action_character.planner.calendar.events[:count]
        return "\n".join(
            [
                f"{event.name} will happen in {event.turn - current_turn} turns"
                for event in events
            ]
        )
