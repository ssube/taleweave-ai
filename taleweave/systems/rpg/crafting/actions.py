from random import randint

from taleweave.context import (
    broadcast,
    get_dungeon_master,
    get_game_systems,
    world_context,
)
from taleweave.generate import generate_item
from taleweave.models.base import dataclass
from taleweave.models.entity import Item


@dataclass
class Recipe:
    ingredients: list[str]
    result: str
    difficulty: int


recipes = {
    "potion": Recipe(["herb", "water"], "potion", 5),
    "sword": Recipe(["metal", "wood"], "sword", 10),
}


def action_craft(item: str) -> str:
    """
    Craft an item using available recipes and inventory items.

    Args:
        item: The name of the item to craft.
    """
    with world_context() as (action_world, _, action_character):
        if item not in recipes:
            return f"There is no recipe to craft a {item}."

        recipe = recipes[item]

        # Check if the character has the required skill level
        skill = randint(1, 20)
        if skill < recipe.difficulty:
            return f"You need a crafting skill level of {recipe.difficulty} to craft {item}."

        # Collect inventory items names
        inventory_items = {item.name for item in action_character.items}

        # Check for sufficient ingredients
        missing_items = [
            item for item in recipe.ingredients if item not in inventory_items
        ]
        if missing_items:
            return f"You are missing {' and '.join(missing_items)} to craft {item}."

        # Deduct the ingredients from inventory
        for ingredient in recipe.ingredients:
            item_to_remove = next(
                item for item in action_character.items if item.name == ingredient
            )
            action_character.items.remove(item_to_remove)

        # Create and add the crafted item to inventory
        result_item = next(
            (item for item in action_character.items if item.name == recipe.result),
            None,
        )
        if result_item:
            new_item = Item(**vars(result_item))  # Copying the item
        else:
            dungeon_master = get_dungeon_master()
            systems = get_game_systems()
            new_item = generate_item(
                dungeon_master, action_world, systems
            )  # TODO: pass crafting recipe and generate from that

        action_character.items.append(new_item)

        broadcast(f"{action_character.name} crafts a {item}.")
        return f"You successfully craft a {item}."
