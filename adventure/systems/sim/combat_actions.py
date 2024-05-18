from adventure.context import (
    action_context,
    broadcast,
    get_agent_for_actor,
    get_dungeon_master,
)
from adventure.utils.search import find_actor_in_room, find_item_in_room
from adventure.utils.world import describe_entity


def action_attack(target: str) -> str:
    """
    Attack a character or item in the room.

    Args:
      target: The name of the character or item to attack.
    """

    with action_context() as (action_room, action_actor):
        # make sure the target is in the room
        target_actor = find_actor_in_room(action_room, target)
        target_item = find_item_in_room(action_room, target)

        dungeon_master = get_dungeon_master()
        if target_actor:
            target_agent = get_agent_for_actor(target_actor)
            if not target_agent:
                raise ValueError(f"no agent found for actor {target_actor.name}")

            reaction = target_agent(
                f"{action_actor.name} is attacking you in the {action_room.name}. How do you react?"
                "Respond with 'fighting', 'fleeing', or 'surrendering'."
            )

            outcome = dungeon_master(
                f"{action_actor.name} attacks {target} in the {action_room.name}. {describe_entity(action_room)}."
                f"{describe_entity(action_actor)}. {describe_entity(target_actor)}."
                f"{target} reacts by {reaction}. What is the outcome of the attack? Describe the result in detail."
            )

            description = (
                f"{action_actor.name} attacks the {target} in the {action_room.name}."
                f"{target} reacts by {reaction}. {outcome}"
            )
            broadcast(description)
            return description

        if target_item:
            outcome = dungeon_master(
                f"{action_actor.name} attacks {target} in the {action_room.name}. {describe_entity(action_room)}."
                f"{describe_entity(action_actor)}. {describe_entity(target_item)}."
                f"What is the outcome of the attack? Describe the result in detail."
            )

            description = f"{action_actor.name} attacks the {target} in the {action_room.name}. {outcome}"
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

    with action_context() as (action_room, action_actor):
        # make sure the target is in the room
        target_actor = find_actor_in_room(action_room, target)
        target_item = find_item_in_room(action_room, target)

        if not target_actor and not target_item:
            return f"{target} is not in the {action_room.name}."

        dungeon_master = get_dungeon_master()
        outcome = dungeon_master(
            f"{action_actor.name} casts {spell} on {target} in the {action_room.name}. {describe_entity(action_room)}."
            f"{describe_entity(action_actor)}. {describe_entity(target_actor) if target_actor else describe_entity(target_item)}."
            f"What is the outcome of the spell? Describe the result in detail."
        )

        description = f"{action_actor.name} casts {spell} on the {target} in the {action_room.name}. {outcome}"
        broadcast(description)
        return description
