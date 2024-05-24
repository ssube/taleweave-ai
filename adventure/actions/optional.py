from logging import getLogger
from typing import Callable, List

from packit.agent import Agent, agent_easy_connect

from adventure.context import (
    action_context,
    broadcast,
    get_agent_for_actor,
    get_dungeon_master,
    get_game_systems,
    has_dungeon_master,
    set_dungeon_master,
    world_context,
)
from adventure.generate import generate_item, generate_room, link_rooms
from adventure.utils.effect import apply_effects
from adventure.utils.search import find_actor_in_room
from adventure.utils.string import normalize_name
from adventure.utils.world import describe_actor, describe_entity

logger = getLogger(__name__)

# this is the fallback dungeon master if none is set
if not has_dungeon_master():
    llm = agent_easy_connect()
    set_dungeon_master(
        Agent(
            "dungeon master",
            "You are the dungeon master in charge of a fantasy world.",
            {},
            llm,
        )
    )


def action_explore(direction: str) -> str:
    """
    Explore the room in a new direction. You can only explore directions that do not already have a portal.

    Args:
        direction: The direction to explore. For example: inside, outside, upstairs, downstairs, trapdoor, portal, etc.
    """

    with world_context() as (action_world, action_room, action_actor):
        dungeon_master = get_dungeon_master()

        if direction in action_room.portals:
            dest_room = action_room.portals[direction]
            return f"You cannot explore {direction} from here, that direction already leads to {dest_room}. Please use the move action to go there."

        try:
            systems = get_game_systems()
            new_room = generate_room(dungeon_master, action_world, systems)
            action_world.rooms.append(new_room)

            # link the rooms together
            link_rooms(dungeon_master, action_world, systems, [new_room])

            broadcast(
                f"{action_actor.name} explores {direction} of {action_room.name} and finds a new room: {new_room.name}"
            )
            return f"You explore {direction} and find a new room: {new_room.name}"
        except Exception:
            logger.exception("error generating room")
            return f"You cannot explore {direction} from here, there is no room in that direction."


def action_search(unused: bool) -> str:
    """
    Search the room for hidden items.
    """

    with world_context() as (action_world, action_room, action_actor):
        dungeon_master = get_dungeon_master()

        if len(action_room.items) > 2:
            return (
                "You find nothing hidden in the room. There is no room for more items."
            )

        try:
            systems = get_game_systems()
            new_item = generate_item(
                dungeon_master,
                action_world,
                systems,
                dest_room=action_room,
            )
            action_room.items.append(new_item)

            broadcast(
                f"{action_actor.name} searches {action_room.name} and finds a new item: {new_item.name}"
            )
            return f"You search the room and find a new item: {new_item.name}"
        except Exception:
            logger.exception("error generating item")
            return "You find nothing hidden in the room."


def action_use(item: str, target: str) -> str:
    """
    Use an item on yourself or another character in the room.

    Args:
        item: The name of the item to use.
        target: The name of the character to use the item on, or "self" to use the item on yourself.
    """
    with action_context() as (action_room, action_actor):
        dungeon_master = get_dungeon_master()

        action_item = next(
            (
                search_item
                for search_item in (action_actor.items + action_room.items)
                if search_item.name == item
            ),
            None,
        )
        if not action_item:
            return f"The {item} item is not available to use."

        if target == "self":
            target_actor = action_actor
            target = action_actor.name
        else:
            target_actor = find_actor_in_room(action_room, target)
            if not target_actor:
                return f"The {target} character is not in the room."

        effect_names = [effect.name for effect in action_item.effects]
        chosen_name = dungeon_master(
            f"{action_actor.name} uses {item} on {target}. "
            f"{item} has the following effects: {effect_names}. "
            "Which effect should be applied? Specify the name of the effect to apply."
            "Do not include the question or any JSON. Only include the name of the effect to apply."
        )
        chosen_name = normalize_name(chosen_name)

        chosen_effect = next(
            (
                search_effect
                for search_effect in action_item.effects
                if normalize_name(search_effect.name) == chosen_name
            ),
            None,
        )
        if not chosen_effect:
            # TODO: should retry the question if the effect is not found
            return f"The {chosen_name} effect is not available to apply."

        try:
            apply_effects(target_actor, [chosen_effect])
        except Exception:
            logger.exception("error applying effect: %s", chosen_effect)
            return f"There was a problem applying the {chosen_name} effect."

        broadcast(
            f"{action_actor.name} uses the {chosen_name} effect of {item} on {target}"
        )
        outcome = dungeon_master(
            f"{action_actor.name} uses the {chosen_name} effect of {item} on {target}. "
            f"{describe_actor(action_actor)}. {describe_actor(target_actor)}. {describe_entity(action_item)}. "
            f"What happens? How does {target} react? Be creative with the results. The outcome can be good, bad, or neutral."
            "Decide based on the characters involved and the item being used."
            "Specify the outcome of the action. Do not include the question or any JSON. Only include the outcome of the action."
        )
        broadcast(f"The action resulted in: {outcome}")

        # make sure both agents remember the outcome
        target_agent = get_agent_for_actor(target_actor)
        if target_agent and target_agent.memory:
            target_agent.memory.append(outcome)

        return outcome


def init() -> List[Callable]:
    """
    Initialize the custom actions.
    """
    return [
        action_explore,
        action_search,
        action_use,
    ]
