import re
from logging import getLogger
from random import shuffle
from typing import List

from taleweave.context import get_current_world, get_dungeon_master
from taleweave.models.entity import Room, WorldEntity
from taleweave.models.event import (
    ActionEvent,
    GameEvent,
    ReplyEvent,
    ResultEvent,
    StatusEvent,
)
from taleweave.utils.search import find_character_in_room, find_item_in_room, find_room
from taleweave.utils.world import describe_entity

logger = getLogger(__name__)


def prompt_from_parameters(
    action_room: Room, parameters: dict[str, bool | float | int | str]
) -> tuple[str, str]:
    pre = []
    post = []

    if "character" in parameters:
        # look up the character
        character_name = str(parameters["character"])
        logger.debug("searching for parameter character: %s", character_name)
        target_character = find_character_in_room(action_room, character_name)
        if target_character:
            logger.debug("adding character to prompt: %s", target_character.name)
            pre.append(f"with {target_character.name}")
            post.append(describe_entity(target_character))

    if "item" in parameters:
        # look up the item
        item_name = str(parameters["item"])
        logger.debug("searching for parameter item: %s", item_name)
        target_item = find_item_in_room(
            action_room,
            item_name,
            include_character_inventory=True,
            include_item_inventory=True,
        )
        if target_item:
            logger.debug("adding item to prompt: %s", target_item.name)
            pre.append(f"using the {target_item.name}")
            post.append(describe_entity(target_item))

    if "target" in parameters:
        # could be a room, character, or item
        target_name = str(parameters["target"])
        logger.debug("searching for parameter target: %s", target_name)

        world = get_current_world()
        if world:
            target_room = find_room(world, target_name)
            if target_room:
                logger.debug("adding room to prompt: %s", target_room.name)
                pre.append(f"in the {target_room.name}")
                post.append(describe_entity(target_room))

            target_character = find_character_in_room(action_room, target_name)
            if target_character:
                logger.debug("adding character to prompt: %s", target_character.name)
                pre.append(f"with {target_character.name}")
                post.append(describe_entity(target_character))

            target_item = find_item_in_room(
                action_room,
                target_name,
                include_character_inventory=True,
                include_item_inventory=True,
            )
            if target_item:
                logger.debug("adding item to prompt: %s", target_item.name)
                pre.append(f"using the {target_item.name}")
                post.append(describe_entity(target_item))

    return (" and ".join(pre) if pre else "", " and ".join(post) if post else "")


def scene_from_event(event: GameEvent) -> str | None:
    logger.debug("generating scene from event: %s", event)

    if isinstance(event, ActionEvent):
        action_name = event.action.removeprefix("action_")
        parameter_pre, parameter_post = prompt_from_parameters(
            event.room, event.parameters
        )

        return (
            f"{event.character.name} uses the {action_name} action {parameter_pre}. "
            "{describe_entity(event.character)}. {describe_entity(event.room)}. {parameter_post}."
        )

    if isinstance(event, ReplyEvent):
        return f"{event.character.name} replies: {event.text}. {describe_entity(event.character)}. {describe_entity(event.room)}."

    if isinstance(event, ResultEvent):
        return f"{event.result}. {describe_entity(event.character)}. {describe_entity(event.room)}."

    if isinstance(event, StatusEvent):
        if event.room:
            if event.character:
                return f"{event.text}. {describe_entity(event.character)}. {describe_entity(event.room)}."

            return f"{event.text}. {describe_entity(event.room)}."

        return event.text

    return None


def scene_from_entity(entity: WorldEntity) -> str:
    logger.debug("generating scene from entity: %s", entity)

    return f"Describe the {entity.type} named {entity.name} in vivid, visual terms. {describe_entity(entity)}"


def make_example_prompts(keywords: List[str], k=5, q=10) -> List[str]:
    logger.debug("generating %s example prompts from keywords: %s", k, keywords)

    examples = []
    for _ in range(k):
        example = list(keywords)
        shuffle(example)
        examples.append(", ".join(example[:q]))

    return examples


def generate_keywords_from_scene(scene: str) -> List[str]:
    logger.debug("generating keywords from scene: %s", scene)

    # TODO: use a gpt2 model to generate keywords from scene

    # hack for now: split on punctuation and whitespace
    words = re.split(r"\W+", scene)

    # downcase and remove empty strings
    words = [word.lower() for word in words if word]
    return words


def generate_prompt_from_scene(scene: str, example_prompts: List[str]) -> str:
    logger.debug(
        "generating prompt from scene and example prompts: %s, %s",
        scene,
        example_prompts,
    )

    # generate prompt from scene and example prompts
    dungeon_master = get_dungeon_master()
    return dungeon_master(
        "Generate a prompt for the following scene:\n"
        "{scene}\n"
        "Here are some example prompts:\n"
        "{examples}\n"
        "Reply with a comma-separated list of keywords that summarize the visual details of the scene."
        "Make sure you describe the location, all of the characters, and any items present using keywords and phrases. "
        "Be creative with the details. Avoid using proper nouns or character names. Describe any actions being taken. "
        "Describe the characters first, then the location, then the other visual details and general atmosphere. "
        "Do not include the question or any JSON. Only include the list of keywords on a single line.",
        examples=example_prompts,
        scene=scene,
    )


def prompt_from_event(event: GameEvent) -> str | None:
    scene = scene_from_event(event)
    if not scene:
        return None

    keywords = generate_keywords_from_scene(scene)
    example_prompts = make_example_prompts(keywords)
    result = generate_prompt_from_scene(scene, example_prompts)
    return result


def prompt_from_entity(entity: WorldEntity) -> str:
    scene = scene_from_entity(entity)
    keywords = generate_keywords_from_scene(scene)
    example_prompts = make_example_prompts(keywords)
    result = generate_prompt_from_scene(scene, example_prompts)
    return result
