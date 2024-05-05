from logging import getLogger
from typing import Callable, List

from packit.agent import Agent, agent_easy_connect

from adventure.context import broadcast, get_agent_for_actor, get_current_context
from adventure.generate import OPPOSITE_DIRECTIONS, generate_item, generate_room

logger = getLogger(__name__)


llm = agent_easy_connect()

# TODO: provide dungeon master with the world theme
dungeon_master = Agent(
    "dungeon master",
    "You are the dungeon master in charge of a fantasy world.",
    {},
    llm,
)


def action_explore(direction: str) -> str:
    """
    Explore the room in a new direction.

    Args:
        direction: The direction to explore: north, south, east, or west.
    """

    current_world, current_room, current_actor = get_current_context()

    if not current_world:
        raise ValueError("No world found")

    if direction in current_room.portals:
        dest_room = current_room.portals[direction]
        return f"You cannot explore {direction} from here, that direction leads to {dest_room}."

    existing_rooms = [room.name for room in current_world.rooms]
    new_room = generate_room(
        dungeon_master, current_world.theme, existing_rooms=existing_rooms
    )
    current_world.rooms.append(new_room)

    # link the rooms together
    current_room.portals[direction] = new_room.name
    new_room.portals[OPPOSITE_DIRECTIONS[direction]] = current_room.name

    broadcast(
        f"{current_actor.name} explores {direction} of {current_room.name} and finds a new room: {new_room.name}"
    )
    return f"You explore {direction} and find a new room: {new_room.name}"


def action_search() -> str:
    """
    Search the room for hidden items.
    """

    action_world, action_room, action_actor = get_current_context()

    if len(action_room.items) > 2:
        return "You find nothing hidden in the room."

    existing_items = [item.name for item in action_room.items]

    new_item = generate_item(
        dungeon_master,
        action_world.theme,
        existing_items=existing_items,
        dest_room=action_room.name,
    )
    action_room.items.append(new_item)

    broadcast(
        f"{action_actor.name} searches {action_room.name} and finds a new item: {new_item.name}"
    )
    return f"You search the room and find a new item: {new_item.name}"


def action_use(item: str, target: str) -> str:
    """
    Use an item on yourself or another character in the room.

    Args:
        item: The name of the item to use.
        target: The name of the character to use the item on, or "self" to use the item on yourself.
    """
    _, action_room, action_actor = get_current_context()

    available_items = [item.name for item in action_actor.items] + [
        item.name for item in action_room.items
    ]

    if item not in available_items:
        return f"The {item} item is not available to use."

    if target == "self":
        target_actor = action_actor
        target = action_actor.name
    else:
        target_actor = next(
            (actor for actor in action_room.actors if actor.name == target), None
        )
        if not target_actor:
            return f"The {target} character is not in the room."

    broadcast(f"{action_actor.name} uses {item} on {target}")
    outcome = dungeon_master(
        f"{action_actor.name} uses {item} on {target}. {action_actor.description}. {target_actor.description}. What happens? How does {target} react? "
        "Specify the outcome of the action. Do not include the question or any JSON. Only include the outcome of the action."
    )
    broadcast(f"The action resulted in: {outcome}")

    # make sure both agents remember the outcome
    target_agent = get_agent_for_actor(target_actor)
    if target_agent:
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
