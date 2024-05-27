from adventure.context import action_context, get_agent_for_actor, get_current_step
from adventure.errors import ActionError
from adventure.models.config import DEFAULT_CONFIG
from adventure.models.planning import CalendarEvent
from adventure.utils.planning import get_recent_notes

actor_config = DEFAULT_CONFIG.world.actor


def take_note(fact: str):
    """
    Remember a fact by recording it in your notes. Facts are critical information about yourself and others that you
    have learned during your adventures. You can review your notes at any time to help you make decisions.

    Args:
        fact: The fact to remember.
    """

    with action_context() as (_, action_actor):
        if fact in action_actor.planner.notes:
            raise ActionError("You already have a note about that fact.")

        if len(action_actor.planner.notes) >= actor_config.note_limit:
            raise ActionError(
                "You have reached the limit of notes you can take. Please erase, replace, or summarize some notes."
            )

        action_actor.planner.notes.append(fact)

        return "You make a note of that fact."


def read_notes(unused: bool, count: int = 10):
    """
    Read your notes to review the facts that you have learned during your adventures.

    Args:
        count: The number of recent notes to read. 10 is usually a good number.
    """

    with action_context() as (_, action_actor):
        facts = get_recent_notes(action_actor, count=count)
        return "\n".join(facts)


def erase_notes(prefix: str) -> str:
    """
    Erase notes that start with a specific prefix.

    Args:
        prefix: The prefix to match notes against.
    """

    with action_context() as (_, action_actor):
        matches = [
            note for note in action_actor.planner.notes if note.startswith(prefix)
        ]
        if not matches:
            return "No notes found with that prefix."

        action_actor.planner.notes[:] = [
            note for note in action_actor.planner.notes if note not in matches
        ]
        return f"Erased {len(matches)} notes."


def replace_note(old: str, new: str) -> str:
    """
    Replace a note with a new note.

    Args:
        old: The old note to replace.
        new: The new note to replace it with.
    """

    with action_context() as (_, action_actor):
        if old not in action_actor.planner.notes:
            return "Note not found."

        action_actor.planner.notes[:] = [
            new if note == old else note for note in action_actor.planner.notes
        ]
        return "Note replaced."


def summarize_notes(limit: int) -> str:
    """
    Summarize your notes by combining similar notes and removing duplicates.

    Args:
        limit: The maximum number of notes to keep.
    """

    with action_context() as (_, action_actor):
        notes = action_actor.planner.notes
        action_agent = get_agent_for_actor(action_actor)

        if not action_agent:
            raise ActionError("Agent missing for actor {action_actor.name}")

        summary = action_agent(
            "Please summarize your notes. Remove any duplicates and combine similar notes. "
            "If a newer note contradicts an older note, keep the newer note. "
            "Clean up your notes so you can focus on the most important facts. "
            "Respond with one note per line. You can have up to {limit} notes, "
            "so make sure you reply with less than {limit} lines. "
            "Your notes are:\n{notes}",
            limit=limit,
            notes=notes,
        )

        new_notes = [note.strip() for note in summary.split("\n") if note.strip()]
        if len(new_notes) > actor_config.note_limit:
            raise ActionError(
                f"Too many notes. You can only have up to {actor_config.note_limit} notes."
            )

        action_actor.planner.notes[:] = new_notes
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

    with action_context() as (_, action_actor):
        # TODO: check for existing events with the same name
        event = CalendarEvent(name, turns)
        action_actor.planner.calendar.events.append(event)
        return f"{name} is scheduled to happen in {turns} turns."


def check_calendar(unused: bool, count: int = 10):
    """
    Read your calendar to see upcoming events that you have scheduled.
    """

    current_turn = get_current_step()

    with action_context() as (_, action_actor):
        events = action_actor.planner.calendar.events[:count]
        return "\n".join(
            [
                f"{event.name} will happen in {event.turn - current_turn} turns"
                for event in events
            ]
        )
