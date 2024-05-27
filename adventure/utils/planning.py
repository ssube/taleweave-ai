from adventure.models.entity import Character


def expire_events(character: Character, current_turn: int):
    """
    Expire events that have already happened.
    """

    events = character.planner.calendar.events
    expired_events = [event for event in events if event.turn < current_turn]
    character.planner.calendar.events[:] = [
        event for event in events if event not in expired_events
    ]

    return expired_events


def get_recent_notes(character: Character, count: int = 3):
    """
    Get the most recent facts from your notes.
    """

    return character.planner.notes[-count:]


def get_upcoming_events(
    character: Character, current_turn: int, upcoming_turns: int = 3
):
    """
    Get a list of upcoming events within a certain number of turns.
    """

    calendar = character.planner.calendar
    # TODO: sort events by turn
    return [
        event
        for event in calendar.events
        if event.turn - current_turn <= upcoming_turns
    ]
