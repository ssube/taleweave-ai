from taleweave.context import action_context
from taleweave.utils.search import find_item_in_character


def action_cook(item: str) -> str:
    """
    Cook an item from your inventory.

    Args:
      item: The name of the item to cook.
    """
    with action_context() as (_, action_character):
        target_item = find_item_in_character(action_character, item)
        if target_item is None:
            return "You don't have the item to cook."

        # Check if the item is edible
        edible = target_item.attributes.get("edible", False)
        if not edible:
            return "You can't cook that."

        # Check if the item is raw
        cooked = target_item.attributes.get("cooked", False)
        if cooked:
            return "That item is already cooked."

        # Cook the item
        target_item.attributes["cooked"] = True
        return f"You cook the {item}."


def action_eat(item: str) -> str:
    """
    Eat an item from your inventory.

    Args:
      item: The name of the item to eat.
    """
    with action_context() as (_, action_character):
        target_item = find_item_in_character(action_character, item)
        if target_item is None:
            return "You don't have the item to eat."

        # Check if the item is edible
        edible = target_item.attributes.get("edible", False)
        if not edible:
            return "You can't eat that."

        # Check if the item is cooked
        cooked = target_item.attributes.get("cooked", False)
        if not cooked:
            return "You can't eat that raw."

        # Check if the item is rotten
        spoiled = target_item.attributes.get("spoiled", False)
        if spoiled:
            return "You can't eat that item, it is rotten."

        # Check if the character is hungry
        hunger = action_character.attributes.get("hunger", None)
        if hunger != "hungry":
            return "You're not hungry."

        # Eat the item
        action_character.items.remove(target_item)
        action_character.attributes["hunger"] = "full"
        return f"You eat the {item}."
