from adventure.context import action_context, broadcast
from adventure.utils.search import find_item_in_actor


def action_read(item_name: str) -> str:
    """
    Read an item like a book or a sign.

    Args:
        item_name: The name of the item to read.
    """
    with action_context() as (_, action_actor):
        item = find_item_in_actor(action_actor, item_name)
        if not item:
            return f"You do not have a {item_name} to read."

        if "text" in item.attributes:
            broadcast(f"{action_actor.name} reads {item_name}")
            return str(item.attributes["text"])

        return f"The {item_name} has nothing to read."
