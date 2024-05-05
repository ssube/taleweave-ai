from adventure.context import get_current_context


def action_cook(item: str) -> str:
    """
    Cook an item from your inventory.

    Args:
      item: The name of the item to cook.
    """
    _, _, action_actor = get_current_context()

    target_item = next((i for i in action_actor.items if i.name == item), None)
    if target_item is None:
        return "You don't have the item to cook."

    # Check if the item is edible
    edible = target_item.attributes.get("edible", None)
    if not edible:
        return "You can't cook that."

    # Check if the item is raw
    if edible == "cooked":
        return "That item is already cooked."

    # Cook the item
    target_item.attributes["edible"] = "cooked"
    return f"You cook the {item}."


def action_eat(item: str) -> str:
    """
    Eat an item from your inventory.

    Args:
      item: The name of the item to eat.
    """
    _, _, action_actor = get_current_context()

    target_item = next((i for i in action_actor.items if i.name == item), None)
    if target_item is None:
        return "You don't have the item to eat."

    # Check if the item is edible
    edible = target_item.attributes.get("edible", None)
    if not edible:
        return "You can't eat that."

    # Check if the item is cooked
    if edible == "raw":
        return "You can't eat that raw."

    if edible == "rotten":
        return "That item is rotten."

    # Check if the actor is hungry
    hunger = action_actor.attributes.get("hunger", None)
    if hunger != "hungry":
        return "You're not hungry."

    # Eat the item
    action_actor.items.remove(target_item)
    action_actor.attributes["hunger"] = "full"
    return f"You eat the {item}."
