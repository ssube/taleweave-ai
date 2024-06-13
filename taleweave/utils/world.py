from logging import getLogger

from taleweave.context import get_game_systems
from taleweave.game_system import FormatPerspective
from taleweave.models.entity import Character, WorldEntity

logger = getLogger(__name__)


def describe_character(
    character: Character,
    perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
) -> str:
    attribute_descriptions = format_attributes(character, perspective=perspective)
    logger.info(
        "describing character: %s, attributes: '%s'",
        character.name,
        attribute_descriptions,
    )

    if perspective == FormatPerspective.SECOND_PERSON:
        character_description = character.backstory
    elif perspective == FormatPerspective.THIRD_PERSON:
        character_description = character.description
    else:
        raise ValueError(f"Perspective {perspective} is not implemented")

    return f"{character_description} {attribute_descriptions}"


def describe_static(entity: WorldEntity) -> str:
    attribute_descriptions = format_attributes(entity)
    logger.info(
        "describing entity: %s, attributes: '%s'",
        entity.name,
        attribute_descriptions,
    )
    return f"{entity.description} {attribute_descriptions}"


def describe_entity(
    entity: WorldEntity,
    perspective: FormatPerspective = FormatPerspective.THIRD_PERSON,
) -> str:
    if isinstance(entity, Character):
        return describe_character(entity, perspective)

    return describe_static(entity)


def format_attributes(
    entity: WorldEntity,
    perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
) -> str:
    systems = get_game_systems()
    attribute_descriptions = [
        system.format(entity, perspective=perspective)
        for system in systems
        if system.format
    ]
    attribute_descriptions = [
        description
        for description in attribute_descriptions
        if len(description.strip()) > 0
    ]

    return f"{'. '.join(attribute_descriptions)}"


def name_entity(
    entity: str | WorldEntity,
) -> str:
    if isinstance(entity, str):
        return entity

    return entity.name
