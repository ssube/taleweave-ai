from json import loads
from logging import getLogger

from packit.utils import could_be_json

from adventure.context import get_actor_agent_for_name, get_current_context

logger = getLogger(__name__)


def action_look(target: str) -> str:
    _, action_room, action_actor = get_current_context()
    logger.info(f"{action_actor.name} looks at {target}")

    if target == action_room.name:
        logger.info(f"{action_actor.name} saw the {action_room.name} room")
        return action_room.description

    for actor in action_room.actors:
        if actor.name == target:
            logger.info(
                f"{action_actor.name} saw the {actor.name} actor in the {action_room.name} room"
            )
            return actor.description

    for item in action_room.items:
        if item.name == target:
            logger.info(
                f"{action_actor.name} saw the {item.name} item in the {action_room.name} room"
            )
            return item.description

    for item in action_actor.items:
        if item.name == target:
            logger.info(
                f"{action_actor.name} saw the {item.name} item in their inventory"
            )
            return item.description

    return "You do not see that item or character in the room."


def action_move(direction: str) -> str:
    action_world, action_room, action_actor = get_current_context()

    destination_name = action_room.portals.get(direction)
    if not destination_name:
        return f"You cannot move {direction} from here."

    destination_room = next(
        (room for room in action_world.rooms if room.name == destination_name), None
    )
    if not destination_room:
        return f"The {destination_name} room does not exist."

    logger.info(f"{action_actor.name} moves {direction} to {destination_name}")
    action_room.actors.remove(action_actor)
    destination_room.actors.append(action_actor)

    return f"You move {direction} and arrive at {destination_name}."


def action_take(item_name: str) -> str:
    _, action_room, action_actor = get_current_context()

    item = next((item for item in action_room.items if item.name == item_name), None)
    if item:
        logger.info(f"{action_actor.name} takes the {item_name} item")
        action_room.items.remove(item)
        action_actor.items.append(item)
        return "You take the {item_name} item and put it in your inventory."
    else:
        return "The {item_name} item is not in the room."


def action_ask(character: str, question: str) -> str:
    # capture references to the current actor and room, because they will be overwritten
    _, action_room, action_actor = get_current_context()

    if not action_actor or not action_room:
        raise ValueError(
            "The current actor and room must be set before calling action_ask"
        )

    # sanity checks
    if character == action_actor.name:
        return "You cannot ask yourself a question. Stop talking to yourself."

    question_actor, question_agent = get_actor_agent_for_name(character)
    if not question_actor:
        return f"The {character} character is not in the room."

    if not question_agent:
        return f"The {character} character does not exist."

    logger.info(f"{action_actor.name} asks {character}: {question}")
    answer = question_agent(
        f"{action_actor.name} asks you: {question}. Reply with your response. "
        f"Do not include the question or any other text, only your reply to {action_actor.name}."
    )

    if could_be_json(answer) and action_tell.__name__ in answer:
        answer = loads(answer).get("parameters", {}).get("message", "")

    if len(answer.strip()) > 0:
        logger.info(f"{character} responds to {action_actor.name}: {answer}")
        return f"{character} responds: {answer}"

    return f"{character} does not respond."


def action_tell(character: str, message: str) -> str:
    # capture references to the current actor and room, because they will be overwritten
    _, action_room, action_actor = get_current_context()

    if not action_actor or not action_room:
        raise ValueError(
            "The current actor and room must be set before calling action_tell"
        )

    # sanity checks
    if character == action_actor.name:
        return "You cannot tell yourself a message. Stop talking to yourself."

    question_actor, question_agent = get_actor_agent_for_name(character)
    if not question_actor:
        return f"The {character} character is not in the room."

    if not question_agent:
        return f"The {character} character does not exist."

    logger.info(f"{action_actor.name} tells {character}: {message}")
    answer = question_agent(
        f"{action_actor.name} tells you: {message}. Reply with your response. "
        f"Do not include the message or any other text, only your reply to {action_actor.name}."
    )

    if could_be_json(answer) and action_tell.__name__ in answer:
        answer = loads(answer).get("parameters", {}).get("message", "")

    if len(answer.strip()) > 0:
        logger.info(f"{character} responds to {action_actor.name}: {answer}")
        return f"{character} responds: {answer}"

    return f"{character} does not respond."


def action_give(character: str, item_name: str) -> str:
    _, action_room, action_actor = get_current_context()

    destination_actor = next(
        (actor for actor in action_room.actors if actor.name == character), None
    )
    if not destination_actor:
        return f"The {character} character is not in the room."

    item = next((item for item in action_actor.items if item.name == item_name), None)
    if not item:
        return f"You do not have the {item_name} item in your inventory."

    logger.info(f"{action_actor.name} gives {character} the {item_name} item")
    action_actor.items.remove(item)
    destination_actor.items.append(item)

    return f"You give the {item_name} item to {character}."
