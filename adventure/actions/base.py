from json import loads
from logging import getLogger

from packit.utils import could_be_json

from adventure.context import (
    action_context,
    broadcast,
    get_actor_agent_for_name,
    world_context,
)
from adventure.utils.search import (
    find_actor_in_room,
    find_item_in_actor,
    find_item_in_room,
    find_room,
)
from adventure.utils.world import describe_entity

logger = getLogger(__name__)


def action_look(target: str) -> str:
    """
    Look at a target in the room or your inventory.

    Args:
        target: The name of the target to look at.
    """

    with action_context() as (action_room, action_actor):
        broadcast(f"{action_actor.name} looks at {target}")

        if target.lower() == action_room.name.lower():
            broadcast(f"{action_actor.name} saw the {action_room.name} room")
            return describe_entity(action_room)

        target_actor = find_actor_in_room(action_room, target)
        if target_actor:
            broadcast(
                f"{action_actor.name} saw the {target_actor.name} actor in the {action_room.name} room"
            )
            return describe_entity(target_actor)

        target_item = find_item_in_room(action_room, target)
        if target_item:
            broadcast(
                f"{action_actor.name} saw the {target_item.name} item in the {action_room.name} room"
            )
            return describe_entity(target_item)

        target_item = find_item_in_actor(action_actor, target)
        if target_item:
            broadcast(
                f"{action_actor.name} saw the {target_item.name} item in their inventory"
            )
            return describe_entity(target_item)

        return "You do not see that item or character in the room."


def action_move(direction: str) -> str:
    """
    Move into another room.

    Args:
        direction: The direction to move in.
    """

    with world_context() as (action_world, action_room, action_actor):
        portal = next(
            (p for p in action_room.portals if p.name.lower() == direction.lower()),
            None,
        )
        if not portal:
            return f"You cannot move {direction} from here."

        destination_room = find_room(action_world, portal.destination)
        if not destination_room:
            return f"The {portal.destination} room does not exist."

        broadcast(f"{action_actor.name} moves {direction} to {destination_room.name}")
        action_room.actors.remove(action_actor)
        destination_room.actors.append(action_actor)

        return f"You move {direction} and arrive at {destination_room.name}."


def action_take(item_name: str) -> str:
    """
    Take an item from the room and put it in your inventory.

    Args:
        item_name: The name of the item to take.
    """
    with action_context() as (action_room, action_actor):
        item = find_item_in_room(action_room, item_name)
        if not item:
            return "The {item_name} item is not in the room."

        broadcast(f"{action_actor.name} takes the {item_name} item")
        action_room.items.remove(item)
        action_actor.items.append(item)
        return "You take the {item_name} item and put it in your inventory."


def action_ask(character: str, question: str) -> str:
    """
    Ask another character a question.

    Args:
        character: The name of the character to ask.
        question: The question to ask them.
    """
    # capture references to the current actor and room, because they will be overwritten
    with action_context() as (_, action_actor):
        # sanity checks
        question_actor, question_agent = get_actor_agent_for_name(character)
        if question_actor == action_actor:
            return "You cannot ask yourself a question. Stop talking to yourself. Try another action."

        if not question_actor:
            return f"The {character} character is not in the room."

        if not question_agent:
            return f"The {character} character does not exist."

        broadcast(f"{action_actor.name} asks {character}: {question}")
        answer = question_agent(
            f"{action_actor.name} asks you: {question}. Reply with your response to them. "
            f"Do not include the question or any JSON. Only include your answer for {action_actor.name}."
        )

        if could_be_json(answer) and action_tell.__name__ in answer:
            answer = loads(answer).get("parameters", {}).get("message", "")

        if len(answer.strip()) > 0:
            broadcast(f"{character} responds to {action_actor.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_tell(character: str, message: str) -> str:
    """
    Tell another character a message.

    Args:
        character: The name of the character to tell.
        message: The message to tell them.
    """
    # capture references to the current actor and room, because they will be overwritten

    with action_context() as (_, action_actor):
        # sanity checks
        question_actor, question_agent = get_actor_agent_for_name(character)
        if question_actor == action_actor:
            return "You cannot tell yourself a message. Stop talking to yourself. Try another action."

        if not question_actor:
            return f"The {character} character is not in the room."

        if not question_agent:
            return f"The {character} character does not exist."

        broadcast(f"{action_actor.name} tells {character}: {message}")
        answer = question_agent(
            f"{action_actor.name} tells you: {message}. Reply with your response to them. "
            f"Do not include the message or any JSON. Only include your reply to {action_actor.name}."
        )

        if could_be_json(answer) and action_tell.__name__ in answer:
            answer = loads(answer).get("parameters", {}).get("message", "")

        if len(answer.strip()) > 0:
            broadcast(f"{character} responds to {action_actor.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_give(character: str, item_name: str) -> str:
    """
    Give an item to another character in the room.

    Args:
        character: The name of the character to give the item to.
        item_name: The name of the item to give.
    """
    with action_context() as (action_room, action_actor):
        destination_actor = find_actor_in_room(action_room, character)
        if not destination_actor:
            return f"The {character} character is not in the room."

        item = find_item_in_actor(action_actor, item_name)
        if not item:
            return f"You do not have the {item_name} item in your inventory."

        broadcast(f"{action_actor.name} gives {character} the {item_name} item.")
        action_actor.items.remove(item)
        destination_actor.items.append(item)

        return f"You give the {item_name} item to {character}."


def action_drop(item_name: str) -> str:
    """
    Drop an item from your inventory into the room.

    Args:
        item_name: The name of the item to drop.
    """

    with action_context() as (action_room, action_actor):
        item = find_item_in_actor(action_actor, item_name)
        if not item:
            return f"You do not have the {item_name} item in your inventory."

        broadcast(f"{action_actor.name} drops the {item_name} item")
        action_actor.items.remove(item)
        action_room.items.append(item)

        return f"You drop the {item_name} item."
