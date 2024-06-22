from taleweave.context import (
    action_context,
    broadcast,
    get_agent_for_character,
    get_dungeon_master,
)
from taleweave.utils.search import find_character_in_room, find_item_in_room
from taleweave.utils.world import describe_entity


def action_attack(target: str) -> str:
    """
    Attack a character or item in the room.

    Args:
      target: The name of the character or item to attack.
    """

    with action_context() as (action_room, action_character):
        # make sure the target is in the room
        target_character = find_character_in_room(action_room, target)
        target_item = find_item_in_room(action_room, target)

        dungeon_master = get_dungeon_master()
        if target_character:
            target_agent = get_agent_for_character(target_character)
            if not target_agent:
                raise ValueError(
                    f"no agent found for character {target_character.name}"
                )

            reaction = target_agent(
                f"{action_character.name} is attacking you in the {action_room.name}. How do you react?"
                "Respond with 'fighting', 'fleeing', or 'surrendering'."
            )

            outcome = dungeon_master(
                f"{action_character.name} attacks {target} in the {action_room.name}. {describe_entity(action_room)}."
                f"{describe_entity(action_character)}. {describe_entity(target_character)}."
                f"{target} reacts by {reaction}. What is the outcome of the attack? Describe the result in detail."
            )

            description = (
                f"{action_character.name} attacks the {target} in the {action_room.name}."
                f"{target} reacts by {reaction}. {outcome}"
            )
            broadcast(description)
            return description

        if target_item:
            outcome = dungeon_master(
                f"{action_character.name} attacks {target} in the {action_room.name}. {describe_entity(action_room)}."
                f"{describe_entity(action_character)}. {describe_entity(target_item)}."
                f"What is the outcome of the attack? Describe the result in detail."
            )

            description = f"{action_character.name} attacks the {target} in the {action_room.name}. {outcome}"
            broadcast(description)
            return description

        return f"{target} is not in the {action_room.name}."


def action_cast(target: str, spell: str) -> str:
    """
    Cast a spell on a character or item in the room.

    Args:
      target: The name of the character or item to cast the spell on.
      spell: The name of the spell to cast.
    """

    with action_context() as (action_room, action_character):
        # make sure the target is in the room
        target_character = find_character_in_room(action_room, target)
        target_item = find_item_in_room(action_room, target)

        if not target_character and not target_item:
            return f"{target} is not in the {action_room.name}."

        dungeon_master = get_dungeon_master()
        outcome = dungeon_master(
            f"{action_character.name} casts {spell} on {target} in the {action_room.name}. {describe_entity(action_room)}."
            f"{describe_entity(action_character)}. {describe_entity(target_character) if target_character else describe_entity(target_item)}."
            f"What is the outcome of the spell? Describe the result in detail."
        )

        description = f"{action_character.name} casts {spell} on the {target} in the {action_room.name}. {outcome}"
        broadcast(description)
        return description
