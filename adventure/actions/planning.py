from adventure.context import action_context, get_current_step
from adventure.models.planning import CalendarEvent


def take_note(fact: str):
    """
    Remember a fact by recording it in your notes. Facts are critical information about yourself and others that you
    have learned during your adventures. You can review your notes at any time to help you make decisions.

    Args:
        fact: The fact to remember.
    """

    with action_context() as (_, action_actor):
        if fact in action_actor.planner.notes:
            return "You already know that."

        action_actor.planner.notes.append(fact)
        return "You make a note of that."


def read_notes(unused: bool, count: int = 10):
    """
    Read your notes to review the facts that you have learned during your adventures.

    Args:
        count: The number of recent notes to read. 10 is usually a good number.
    """

    facts = get_recent_notes(count=count)
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


def schedule_event(name: str, turns: int):
    """
    Schedule an event to happen at a specific turn. Events are important occurrences that can affect the world in
    significant ways. You will be notified about upcoming events so you can plan accordingly.

    Args:
        name: The name of the event.
        turns: The number of turns until the event happens.
    """

    with action_context() as (_, action_actor):
        # TODO: check for existing events with the same name
        event = CalendarEvent(name, turns)
        action_actor.planner.calendar.events.append(event)
        return f"{name} is scheduled to happen in {turns} turns."


def read_calendar(unused: bool, count: int = 10):
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


def get_upcoming_events(turns: int = 3):
    """
    Get a list of upcoming events within a certain number of turns.

    Args:
        turns: The number of turns to look ahead for events.
    """

    current_turn = get_current_step()

    with action_context() as (_, action_actor):
        calendar = action_actor.planner.calendar
        # TODO: sort events by turn
        return [
            event for event in calendar.events if event.turn - current_turn <= turns
        ]


def get_recent_notes(count: int = 3):
    """
    Get the most recent facts from your notes.

    Args:
        history: The number of recent facts to retrieve.
    """

    with action_context() as (_, action_actor):
        return action_actor.planner.notes[-count:]
