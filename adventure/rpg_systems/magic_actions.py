from random import randint

from adventure.context import broadcast, get_current_context, get_dungeon_master
from adventure.search import find_actor_in_room


def action_cast(spell: str, target: str) -> str:
    """
    Cast a spell on a target.

    Args:
        spell: The name of the spell to cast.
        target: The target of the spell.
    """
    _, action_room, action_actor = get_current_context()

    target_actor = find_actor_in_room(action_room, target)
    dungeon_master = get_dungeon_master()

    # Check for spell availability and mana costs
    if spell not in action_actor.attributes["spells"]:
        return f"You do not know the spell '{spell}'."
    if action_actor.attributes["mana"] < action_actor.attributes["spells"][spell]:
        return "You do not have enough mana to cast this spell."

    action_actor.attributes["mana"] -= action_actor.attributes["spells"][spell]
    # Get flavor text from the dungeon master
    flavor_text = dungeon_master(f"Describe the effects of {spell} on {target}.")
    broadcast(f"{action_actor.name} casts {spell} on {target}. {flavor_text}")

    # Apply effects based on the spell
    if spell == "heal" and target_actor:
        heal_amount = randint(10, 30)
        target_actor.attributes["health"] += heal_amount
        return f"{target} is healed for {heal_amount} points."

    return f"{spell} was successfully cast on {target}."
