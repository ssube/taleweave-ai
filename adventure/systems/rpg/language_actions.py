from adventure.context import action_context, broadcast
from adventure.utils.search import find_item_in_actor


def action_read(item: str) -> str:
    """
    Read an item like a book or a sign.

    Args:
        item: The name of the item to read.
    """
    with action_context() as (_, action_actor):
        action_item = find_item_in_actor(action_actor, item)
        if not action_item:
            return f"You do not have a {item} to read."

        if "text" in action_item.attributes:
            broadcast(f"{action_actor.name} reads {item}")
            return str(action_item.attributes["text"])

        return f"The {item} has nothing to read."
