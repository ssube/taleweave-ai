from logging import getLogger

from taleweave.context import (
    action_context,
    broadcast,
    get_agent_for_character,
    get_character_agent_for_name,
    world_context,
)
from taleweave.errors import ActionError
from taleweave.utils.conversation import loop_conversation
from taleweave.utils.search import (
    find_character_in_room,
    find_item_in_character,
    find_item_in_room,
    find_room,
)
from taleweave.utils.string import normalize_name
from taleweave.utils.world import describe_entity

logger = getLogger(__name__)

MAX_CONVERSATION_STEPS = 3


def action_look(target: str) -> str:
    """
    Look at a target in the room or your inventory.

    Args:
        target: The name of the target to look at.
    """

    with action_context() as (action_room, action_character):
        broadcast(f"{action_character.name} looks at {target}")

        if normalize_name(target) == normalize_name(action_room.name):
            broadcast(f"{action_character.name} saw the {action_room.name} room")
            return describe_entity(action_room)

        target_character = find_character_in_room(action_room, target)
        if target_character:
            broadcast(
                f"{action_character.name} saw the {target_character.name} character in the {action_room.name} room"
            )
            return describe_entity(target_character)

        target_item = find_item_in_room(action_room, target)
        if target_item:
            broadcast(
                f"{action_character.name} saw the {target_item.name} item in the {action_room.name} room"
            )
            return describe_entity(target_item)

        target_item = find_item_in_character(action_character, target)
        if target_item:
            broadcast(
                f"{action_character.name} saw the {target_item.name} item in their inventory"
            )
            return describe_entity(target_item)

        return "You do not see that item or character in the room."


def action_move(direction: str) -> str:
    """
    Move into another room.

    Args:
        direction: The direction to move in.
    """

    with world_context() as (action_world, action_room, action_character):
        portal = next(
            (
                p
                for p in action_room.portals
                if normalize_name(p.name) == normalize_name(direction)
            ),
            None,
        )
        if not portal:
            raise ActionError(f"You cannot move {direction} from here.")

        destination_room = find_room(action_world, portal.destination)
        if not destination_room:
            raise ActionError(f"The {portal.destination} room does not exist.")

        broadcast(
            f"{action_character.name} moves through {direction} to {destination_room.name}"
        )
        action_room.characters.remove(action_character)
        destination_room.characters.append(action_character)

        return (
            f"You move through the {direction} and arrive at {destination_room.name}."
        )


def action_take(item: str) -> str:
    """
    Take an item from the room and put it in your inventory.

    Args:
        item: The name of the item to take.
    """
    with action_context() as (action_room, action_character):
        action_item = find_item_in_room(action_room, item)
        if not action_item:
            raise ActionError(f"The {item} item is not in the room.")

        broadcast(f"{action_character.name} takes the {item} item")
        action_room.items.remove(action_item)
        action_character.items.append(action_item)
        return f"You take the {item} item and put it in your inventory."


def action_ask(character: str, question: str) -> str:
    """
    Ask another character a question.

    Args:
        character: The name of the character to ask. You cannot ask yourself questions.
        question: The question to ask them.
    """
    # capture references to the current character and room, because they will be overwritten
    with action_context() as (action_room, action_character):
        # sanity checks
        question_character, question_agent = get_character_agent_for_name(character)
        if question_character == action_character:
            raise ActionError(
                "You cannot ask yourself a question. Stop talking to yourself. Try another action."
            )

        if not question_character:
            raise ActionError(f"The {character} character is not in the room.")

        if not question_agent:
            raise ActionError(f"The {character} character does not exist.")

        broadcast(f"{action_character.name} asks {character}: {question}")
        first_prompt = (
            "{last_character.name} asks you: {response}\n"
            "Reply with your response to them. Reply with 'END' to end the conversation. "
            "Do not include the question or any JSON. Only include your answer for {last_character.name}."
        )
        reply_prompt = (
            "{last_character.name} continues the conversation with you. They reply: {response}\n"
            "Reply with your response to them. Reply with 'END' to end the conversation. "
            "Do not include the question or any JSON. Only include your answer for {last_character.name}."
        )

        action_agent = get_agent_for_character(action_character)
        answer = loop_conversation(
            action_room,
            [question_character, action_character],
            [question_agent, action_agent],
            action_character,
            first_prompt,
            reply_prompt,
            question,
            "Goodbye",
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=MAX_CONVERSATION_STEPS,
        )

        if answer:
            broadcast(f"{character} responds to {action_character.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_tell(character: str, message: str) -> str:
    """
    Tell another character a message.

    Args:
        character: The name of the character to tell. You cannot talk to yourself.
        message: The message to tell them.
    """
    # capture references to the current character and room, because they will be overwritten

    with action_context() as (action_room, action_character):
        # sanity checks
        question_character, question_agent = get_character_agent_for_name(character)
        if question_character == action_character:
            raise ActionError(
                "You cannot tell yourself a message. Stop talking to yourself. Try another action."
            )

        if not question_character:
            raise ActionError(f"The {character} character is not in the room.")

        if not question_agent:
            raise ActionError(f"The {character} character does not exist.")

        broadcast(f"{action_character.name} tells {character}: {message}")
        first_prompt = (
            "{last_character.name} starts a conversation with you. They say: {response}\n"
            "Reply with your response to them. "
            "Do not include the message or any JSON. Only include your reply to {last_character.name}."
        )
        reply_prompt = (
            "{last_character.name} continues the conversation with you. They reply: {response}\n"
            "Reply with your response to them. "
            "Do not include the message or any JSON. Only include your reply to {last_character.name}."
        )

        action_agent = get_agent_for_character(action_character)
        answer = loop_conversation(
            action_room,
            [question_character, action_character],
            [question_agent, action_agent],
            action_character,
            first_prompt,
            reply_prompt,
            message,
            "Goodbye",
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=MAX_CONVERSATION_STEPS,
        )

        if answer:
            broadcast(f"{character} responds to {action_character.name}: {answer}")
            return f"{character} responds: {answer}"

        return f"{character} does not respond."


def action_give(character: str, item: str) -> str:
    """
    Give an item to another character in the room.

    Args:
        character: The name of the character to give the item to.
        item: The name of the item to give.
    """
    with action_context() as (action_room, action_character):
        destination_character = find_character_in_room(action_room, character)
        if not destination_character:
            raise ActionError(f"The {character} character is not in the room.")

        if destination_character == action_character:
            raise ActionError(
                "You cannot give an item to yourself. Try another action."
            )

        action_item = find_item_in_character(action_character, item)
        if not action_item:
            raise ActionError(f"You do not have the {item} item in your inventory.")

        broadcast(f"{action_character.name} gives {character} the {item} item.")
        action_character.items.remove(action_item)
        destination_character.items.append(action_item)

        return f"You give the {item} item to {character}."


def action_drop(item: str) -> str:
    """
    Drop an item from your inventory into the room.

    Args:
        item: The name of the item to drop.
    """

    with action_context() as (action_room, action_character):
        action_item = find_item_in_character(action_character, item)
        if not action_item:
            raise ActionError(f"You do not have the {item} item in your inventory.")

        broadcast(f"{action_character.name} drops the {item} item")
        action_character.items.remove(action_item)
        action_room.items.append(action_item)

        return f"You drop the {item} item."
