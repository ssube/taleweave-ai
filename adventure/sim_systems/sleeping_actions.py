from adventure.context import action_context, get_dungeon_master
from adventure.utils.world import describe_entity


def action_sleep(unused: bool) -> str:
    """
    Sleep until you are rested.
    """

    with action_context() as (action_room, action_actor):
        dungeon_master = get_dungeon_master()
        outcome = dungeon_master(
            f"{action_actor.name} sleeps in the {action_room.name}. {describe_entity(action_room)}. {describe_entity(action_actor)}"
            "How rested are they? Respond with 'rested' or 'tired'."
        )

        action_actor.attributes["rested"] = outcome
        return f"You sleep in the {action_room.name} and wake up feeling {outcome}"
