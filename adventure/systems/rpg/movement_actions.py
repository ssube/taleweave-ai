from random import randint

from adventure.context import action_context, broadcast, get_dungeon_master
from adventure.utils.search import find_item_in_room


def action_climb(target: str) -> str:
    """
    Climb a structure or natural feature.

    Args:
        target: The object or feature to climb.
    """
    with action_context() as (action_room, action_character):
        dungeon_master = get_dungeon_master()
        # Assume 'climbable' is an attribute that marks climbable targets
        climbable_feature = find_item_in_room(action_room, target)

        if climbable_feature and climbable_feature.attributes.get("climbable", False):
            climb_difficulty = int(climbable_feature.attributes.get("difficulty", 5))
            climb_roll = randint(1, 20)

            # Get flavor text for the climb attempt
            flavor_text = dungeon_master(
                f"Describe {action_character.name}'s attempt to climb {target}."
            )
            if climb_roll > climb_difficulty:
                broadcast(
                    f"{action_character.name} successfully climbs the {target}. {flavor_text}"
                )
                return f"You successfully climb the {target}."
            else:
                broadcast(
                    f"{action_character.name} fails to climb the {target}. {flavor_text}"
                )
                return f"You fail to climb the {target}."
        else:
            return f"The {target} is not climbable."
