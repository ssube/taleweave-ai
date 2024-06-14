from logging import getLogger

from taleweave.context import (
    action_context,
    broadcast,
    get_agent_for_character,
    get_character_agent_for_name,
    get_game_config,
    get_prompt,
    world_context,
)
from taleweave.errors import ActionError
from taleweave.utils.conversation import loop_conversation
from taleweave.utils.search import (
    find_character_in_room,
    find_item_in_character,
    find_item_in_room,
    find_portal_in_room,
    find_room,
)
from taleweave.utils.string import normalize_name
from taleweave.utils.template import format_prompt

logger = getLogger(__name__)


def action_examine(target: str) -> str:
    """
    Examine the room, a character, or an item (in the room or in your inventory).

    Args:
        target: The name of the target to look at.
    """

    with action_context() as (action_room, action_character):
        broadcast(
            format_prompt(
                "action_examine_broadcast_action",
                action_character=action_character,
                action_room=action_room,
                target=target,
            )
        )

        # TODO: allow "the room" as a target
        if normalize_name(target) == normalize_name(action_room.name):
            broadcast(
                format_prompt(
                    "action_examine_broadcast_room",
                    action_character=action_character,
                    action_room=action_room,
                )
            )
            return format_prompt("action_examine_result_room", target_room=action_room)

        # TODO: allow "self" and "myself" as a target
        target_character = find_character_in_room(action_room, target)
        if target_character:
            broadcast(
                format_prompt(
                    "action_examine_broadcast_character",
                    action_character=action_character,
                    action_room=action_room,
                    target_character=target_character,
                )
            )
            return format_prompt(
                "action_examine_result_character", target_character=target_character
            )

        target_item = find_item_in_room(action_room, target)
        if target_item:
            broadcast(
                format_prompt(
                    "action_examine_broadcast_item",
                    action_character=action_character,
                    action_room=action_room,
                    target_item=target_item,
                )
            )
            return format_prompt("action_examine_result_item", target_item=target_item)

        target_item = find_item_in_character(action_character, target)
        if target_item:
            broadcast(
                format_prompt(
                    "action_examine_broadcast_inventory",
                    action_character=action_character,
                    action_room=action_room,
                    target_item=target_item,
                )
            )
            return format_prompt(
                "action_examine_result_inventory", target_item=target_item
            )

        return format_prompt("action_examine_error_target", target=target)


def action_move(direction: str) -> str:
    """
    Move into another room.

    Args:
        direction: The direction to move in.
    """

    with world_context() as (action_world, action_room, action_character):
        portal = find_portal_in_room(action_room, direction)
        if not portal:
            portals = [p.name for p in action_room.portals]
            raise ActionError(
                format_prompt(
                    "action_move_error_direction", direction=direction, portals=portals
                )
            )

        dest_room = find_room(action_world, portal.destination)
        if not dest_room:
            raise ActionError(
                format_prompt(
                    "action_move_error_room",
                    direction=direction,
                    portal=portal,
                )
            )

        broadcast(
            format_prompt(
                "action_move_broadcast",
                action_character=action_character,
                dest_room=dest_room,
                direction=direction,
            )
        )
        action_room.characters.remove(action_character)
        dest_room.characters.append(action_character)

        return format_prompt(
            "action_move_result", direction=direction, dest_room=dest_room
        )


def action_take(item: str) -> str:
    """
    Pick up an item from the room and put it in your inventory.

    Args:
        item: The name of the item to take.
    """
    with action_context() as (action_room, action_character):
        action_item = find_item_in_room(action_room, item)
        if not action_item:
            raise ActionError(format_prompt("action_take_error_item", item=item))

        broadcast(
            format_prompt(
                "action_take_broadcast",
                action_character=action_character,
                action_room=action_room,
                item=item,
            )
        )
        action_room.items.remove(action_item)
        action_character.items.append(action_item)

        return format_prompt("action_take_result", item=item)


def action_ask(character: str, question: str) -> str:
    """
    Ask another character a question.

    Args:
        character: The name of the character to ask. You cannot ask yourself questions.
        question: The question to ask them.
    """
    config = get_game_config()

    with action_context() as (action_room, action_character):
        # sanity checks
        question_character = find_character_in_room(action_room, character)
        if not question_character:
            raise ActionError(
                format_prompt("action_ask_error_target", character=character)
            )

        if question_character == action_character:
            raise ActionError(format_prompt("action_ask_error_self"))

        question_agent = get_agent_for_character(question_character)
        if not question_agent:
            raise ActionError(
                format_prompt("action_ask_error_agent", character=character)
            )

        broadcast(
            format_prompt(
                "action_ask_broadcast",
                action_character=action_character,
                character=character,
                question=question,
            )
        )
        first_prompt = get_prompt("action_ask_conversation_first")
        reply_prompt = get_prompt("action_ask_conversation_reply")
        end_prompt = get_prompt("action_ask_conversation_end")

        action_agent = get_agent_for_character(action_character)
        result = loop_conversation(
            action_room,
            [question_character, action_character],
            [question_agent, action_agent],
            action_character,
            first_prompt,
            reply_prompt,
            question,
            end_prompt,
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=config.world.character.conversation_limit,
        )

        if result:
            return result

        return format_prompt("action_ask_ignore", character=character)


def action_tell(character: str, message: str) -> str:
    """
    Tell another character a message.

    Args:
        character: The name of the character to tell. You cannot talk to yourself.
        message: The message to tell them.
    """
    config = get_game_config()

    with action_context() as (action_room, action_character):
        # sanity checks
        question_character, question_agent = get_character_agent_for_name(character)
        if question_character == action_character:
            raise ActionError(format_prompt("action_tell_error_self"))

        if not question_character:
            raise ActionError(
                format_prompt("action_tell_error_target", character=character)
            )

        if not question_agent:
            raise ActionError(
                format_prompt("action_tell_error_agent", character=character)
            )

        broadcast(f"{action_character.name} tells {character}: {message}")
        first_prompt = get_prompt("action_tell_conversation_first")
        reply_prompt = get_prompt("action_tell_conversation_reply")
        end_prompt = get_prompt("action_tell_conversation_end")

        action_agent = get_agent_for_character(action_character)
        result = loop_conversation(
            action_room,
            [question_character, action_character],
            [question_agent, action_agent],
            action_character,
            first_prompt,
            reply_prompt,
            message,
            end_prompt,
            echo_function=action_tell.__name__,
            echo_parameter="message",
            max_length=config.world.character.conversation_limit,
        )

        if result:
            return result

        return format_prompt("action_tell_ignore", character=character)


def action_give(character: str, item: str) -> str:
    """
    Give an item in your inventory to another character in the room.

    Args:
        character: The name of the character to give the item to.
        item: The name of the item to give.
    """
    with action_context() as (action_room, action_character):
        destination_character = find_character_in_room(action_room, character)
        if not destination_character:
            raise ActionError(
                format_prompt("action_give_error_target", character=character)
            )

        if destination_character == action_character:
            raise ActionError(format_prompt("action_give_error_self"))

        action_item = find_item_in_character(action_character, item)
        if not action_item:
            raise ActionError(format_prompt("action_give_error_item", item=item))

        broadcast(
            format_prompt(
                "action_give_broadcast",
                action_character=action_character,
                character=character,
                item=item,
            )
        )
        action_character.items.remove(action_item)
        destination_character.items.append(action_item)

        return format_prompt("action_give_result", character=character, item=item)


def action_drop(item: str) -> str:
    """
    Drop an item from your inventory and leave it in the current room.

    Args:
        item: The name of the item to drop.
    """

    with action_context() as (action_room, action_character):
        action_item = find_item_in_character(action_character, item)
        if not action_item:
            raise ActionError(format_prompt("action_drop_error_item", item=item))

        broadcast(
            format_prompt(
                "action_drop_broadcast", action_character=action_character, item=item
            )
        )
        action_character.items.remove(action_item)
        action_room.items.append(action_item)

        return format_prompt("action_drop_result", item=item)
