from taleweave.context import action_context, broadcast
from taleweave.utils.search import find_item_in_character


def action_read(item: str) -> str:
    """
    Read an item like a book or a sign.

    Args:
        item: The name of the item to read.
    """
    with action_context() as (_, action_character):
        action_item = find_item_in_character(action_character, item)
        if not action_item:
            return f"You do not have a {item} to read."

        if "text" in action_item.attributes:
            broadcast(f"{action_character.name} reads {item}")
            return str(action_item.attributes["text"])

        return f"The {item} has nothing to read."
