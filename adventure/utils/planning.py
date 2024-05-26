from adventure.models.entity import Actor


def expire_events(actor: Actor, current_turn: int):
    """
    Expire events that have already happened.
    """

    events = actor.planner.calendar.events
    expired_events = [event for event in events if event.turn < current_turn]
    actor.planner.calendar.events[:] = [
        event for event in events if event not in expired_events
    ]

    return expired_events


def get_recent_notes(actor: Actor, count: int = 3):
    """
    Get the most recent facts from your notes.
    """

    return actor.planner.notes[-count:]


def get_upcoming_events(actor: Actor, current_turn: int, upcoming_turns: int = 3):
    """
    Get a list of upcoming events within a certain number of turns.
    """

    calendar = actor.planner.calendar
    # TODO: sort events by turn
    return [
        event
        for event in calendar.events
        if event.turn - current_turn <= upcoming_turns
    ]
