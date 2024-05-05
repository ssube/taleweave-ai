from adventure.context import get_current_context, get_dungeon_master


def action_wash() -> str:
    """
    Wash yourself.
    """

    _, action_room, action_actor = get_current_context()
    hygiene = action_actor.attributes.get("hygiene", "clean")

    dungeon_master = get_dungeon_master()
    outcome = dungeon_master(
        f"{action_actor.name} washes themselves in the {action_room.name}. {action_room.description}. {action_actor.description}"
        f"{action_actor.name} was {hygiene} to start with. How clean are they after washing? Respond with 'clean' or 'dirty'."
        "If the room has a shower or running water, they should be cleaner. If the room is dirty, they should end up dirtier."
    )

    action_actor.attributes["clean"] = outcome.strip().lower()
    return f"You wash yourself in the {action_room.name} and feel {outcome}"
