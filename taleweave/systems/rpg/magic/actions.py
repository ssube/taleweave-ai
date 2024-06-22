from random import randint

from taleweave.context import action_context, broadcast, get_dungeon_master
from taleweave.utils.search import find_character_in_room


def action_cast(spell: str, target: str) -> str:
    """
    Cast a spell on a target.

    Args:
        spell: The name of the spell to cast.
        target: The target of the spell.
    """
    with action_context() as (action_room, action_character):
        target_character = find_character_in_room(action_room, target)
        dungeon_master = get_dungeon_master()

        # Check for spell availability and mana costs
        if spell not in action_character.attributes["spells"]:
            return f"You do not know the spell '{spell}'."
        if (
            action_character.attributes["mana"]
            < action_character.attributes["spells"][spell]
        ):
            return "You do not have enough mana to cast this spell."

        action_character.attributes["mana"] -= action_character.attributes["spells"][
            spell
        ]
        # Get flavor text from the dungeon master
        flavor_text = dungeon_master(f"Describe the effects of {spell} on {target}.")
        broadcast(f"{action_character.name} casts {spell} on {target}. {flavor_text}")

        # Apply effects based on the spell
        if spell == "heal" and target_character:
            heal_amount = randint(10, 30)
            target_character.attributes["health"] += heal_amount
            return f"{target} is healed for {heal_amount} points."

        return f"{spell} was successfully cast on {target}."
