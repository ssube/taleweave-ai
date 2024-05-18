from random import randint

from adventure.context import broadcast, get_dungeon_master, world_context
from adventure.generate import generate_item
from adventure.models.base import dataclass
from adventure.models.entity import Item


@dataclass
class Recipe:
    ingredients: list[str]
    result: str
    difficulty: int


recipes = {
    "potion": Recipe(["herb", "water"], "potion", 5),
    "sword": Recipe(["metal", "wood"], "sword", 10),
}


def action_craft(item_name: str) -> str:
    """
    Craft an item using available recipes and inventory items.

    Args:
        item_name: The name of the item to craft.
    """
    with world_context() as (action_world, _, action_actor):
        if item_name not in recipes:
            return f"There is no recipe to craft a {item_name}."

        recipe = recipes[item_name]

        # Check if the actor has the required skill level
        skill = randint(1, 20)
        if skill < recipe.difficulty:
            return f"You need a crafting skill level of {recipe.difficulty} to craft {item_name}."

        # Collect inventory items names
        inventory_items = {item.name for item in action_actor.items}

        # Check for sufficient ingredients
        missing_items = [
            item for item in recipe.ingredients if item not in inventory_items
        ]
        if missing_items:
            return (
                f"You are missing {' and '.join(missing_items)} to craft {item_name}."
            )

        # Deduct the ingredients from inventory
        for ingredient in recipe.ingredients:
            item_to_remove = next(
                item for item in action_actor.items if item.name == ingredient
            )
            action_actor.items.remove(item_to_remove)

        # Create and add the crafted item to inventory
        result_item = next(
            (item for item in action_actor.items if item.name == recipe.result), None
        )
        if result_item:
            new_item = Item(**vars(result_item))  # Copying the item
        else:
            dungeon_master = get_dungeon_master()
            new_item = generate_item(
                dungeon_master, action_world.theme
            )  # TODO: pass recipe item

        action_actor.items.append(new_item)

        broadcast(f"{action_actor.name} crafts a {item_name}.")
        return f"You successfully craft a {item_name}."
