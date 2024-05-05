from adventure.context import get_current_context, get_dungeon_master


def action_sleep() -> str:
    """
    Sleep until you are rested.
    """

    _, action_room, action_actor = get_current_context()

    dungeon_master = get_dungeon_master()
    outcome = dungeon_master(
        f"{action_actor.name} sleeps in the {action_room.name}. {action_room.description}. {action_actor.description}"
        "How rested are they? Respond with 'rested' or 'tired'."
    )

    action_actor.attributes["rested"] = outcome
    return f"You sleep in the {action_room.name} and wake up feeling {outcome}"
