from logging import getLogger

from adventure.context import (
    action_context,
    broadcast,
    get_actor_agent_for_name,
    get_agent_for_actor,
    world_context,
)
from adventure.utils.conversation import loop_conversation
from adventure.utils.search import (
    find_actor_in_room,
    find_item_in_actor,
    find_item_in_room,
    find_room,
)
from adventure.utils.string import normalize_name
from adventure.utils.world import describe_entity

logger = getLogger(__name__)

MAX_CONVERSATION_STEPS = 3


def action_look(target: str) -> str:
    """
    Look at a target in the room or your inventory.

    Args:
        target: The name of the target to look at.
    """

    with action_context() as (action_room, action_actor):
        broadcast(f"{action_actor.name} looks at {target}")

        if normalize_name(target) == normalize_name(action_room.name):
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
            (
                p
                for p in action_room.portals
                if normalize_name(p.name) == normalize_name(direction)
            ),
            None,
        )
        if not portal:
            return f"You cannot move {direction} from here."

        destination_room = find_room(action_world, portal.destination)
        if not destination_room:
            return f"The {portal.destination} room does not exist."

        broadcast(
            f"{action_actor.name} moves through {direction} to {destination_room.name}"
        )
        action_room.actors.remove(action_actor)
        destination_room.actors.append(action_actor)

        return (
            f"You move through the {direction} and arrive at {destination_room.name}."
        )


def action_take(item: str) -> str:
    """
    Take an item from the room and put it in your inventory.

    Args:
        item: The name of the item to take.
    """
    with action_context() as (action_room, action_actor):
        action_item = find_item_in_room(action_room, item)
        if not action_item:
            return f"The {item} item is not in the room."

        broadcast(f"{action_actor.name} takes the {item} item")
        action_room.items.remove(action_item)
        action_actor.items.append(action_item)
        return f"You take the {item} item and put it in your inventory."


def action_ask(character: str, question: str) -> str:
    """
    Ask another character a question.

    Args:
        character: The name of the character to ask. You cannot ask yourself questions.
        question: The question to ask them.
    """
    # capture references to the current actor and room, because they will be overwritten
    with action_context() as (action_room, action_actor):
        # sanity checks
        question_actor, question_agent = get_actor_agent_for_name(character)
        if question_actor == action_actor:
            return "You cannot ask yourself a question. Stop talking to yourself. Try another action."

        if not question_actor:
            return f"The {character} character is not in the room."

        if not question_agent:
            return f"The {character} character does not exist."

        broadcast(f"{action_actor.name} asks {character}: {question}")
        first_prompt = (
            "{last_actor.name} asks you: {response}\n"
            "Reply with your response to them. Reply with 'END' to end the conversation. "
            "Do not include the question or any JSON. Only include your answer for {last_actor.name}."
        )
        reply_prompt = (
            "{last_actor.name} continues the conversation with you. They reply: {response}\n"
            "Reply with your response to them. Reply with 'END' to end the conversation. "
            "Do not include the question or any JSON. Only include your answer for {last_actor.name}."
        )

        action_agent = get_agent_for_actor(action_actor)
        answer = loop_conversation(
            action_room,
            [question_actor, action_actor],
            [question_agent, action_agent],
            action_actor,
            first_prompt,
            reply_prompt,
            question,
            "Goodbye",
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=MAX_CONVERSATION_STEPS,
        )

        if answer:
            broadcast(f"{character} responds to {action_actor.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_tell(character: str, message: str) -> str:
    """
    Tell another character a message.

    Args:
        character: The name of the character to tell. You cannot talk to yourself.
        message: The message to tell them.
    """
    # capture references to the current actor and room, because they will be overwritten

    with action_context() as (action_room, action_actor):
        # sanity checks
        question_actor, question_agent = get_actor_agent_for_name(character)
        if question_actor == action_actor:
            return "You cannot tell yourself a message. Stop talking to yourself. Try another action."

        if not question_actor:
            return f"The {character} character is not in the room."

        if not question_agent:
            return f"The {character} character does not exist."

        broadcast(f"{action_actor.name} tells {character}: {message}")
        first_prompt = (
            "{last_actor.name} starts a conversation with you. They say: {response}\n"
            "Reply with your response to them. "
            "Do not include the message or any JSON. Only include your reply to {last_actor.name}."
        )
        reply_prompt = (
            "{last_actor.name} continues the conversation with you. They reply: {response}\n"
            "Reply with your response to them. "
            "Do not include the message or any JSON. Only include your reply to {last_actor.name}."
        )

        action_agent = get_agent_for_actor(action_actor)
        answer = loop_conversation(
            action_room,
            [question_actor, action_actor],
            [question_agent, action_agent],
            action_actor,
            first_prompt,
            reply_prompt,
            message,
            "Goodbye",
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=MAX_CONVERSATION_STEPS,
        )

        if answer:
            broadcast(f"{character} responds to {action_actor.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_give(character: str, item: str) -> str:
    """
    Give an item to another character in the room.

    Args:
        character: The name of the character to give the item to.
        item: The name of the item to give.
    """
    with action_context() as (action_room, action_actor):
        destination_actor = find_actor_in_room(action_room, character)
        if not destination_actor:
            return f"The {character} character is not in the room."

        action_item = find_item_in_actor(action_actor, item)
        if not action_item:
            return f"You do not have the {item} item in your inventory."

        broadcast(f"{action_actor.name} gives {character} the {item} item.")
        action_actor.items.remove(action_item)
        destination_actor.items.append(action_item)

        return f"You give the {item} item to {character}."


def action_drop(item: str) -> str:
    """
    Drop an item from your inventory into the room.

    Args:
        item: The name of the item to drop.
    """

    with action_context() as (action_room, action_actor):
        action_item = find_item_in_actor(action_actor, item)
        if not action_item:
            return f"You do not have the {item} item in your inventory."

        broadcast(f"{action_actor.name} drops the {item} item")
        action_actor.items.remove(action_item)
        action_room.items.append(action_item)

        return f"You drop the {item} item."
