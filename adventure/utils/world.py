from logging import getLogger

from adventure.context import get_game_systems
from adventure.game_system import FormatPerspective
from adventure.models.entity import Actor, WorldEntity

logger = getLogger(__name__)


def describe_actor(
    actor: Actor, perspective: FormatPerspective = FormatPerspective.SECOND_PERSON
) -> str:
    attribute_descriptions = format_attributes(actor, perspective=perspective)
    logger.info("describing actor: %s, %s", actor, attribute_descriptions)

    if perspective == FormatPerspective.SECOND_PERSON:
        actor_description = actor.backstory
    elif perspective == FormatPerspective.THIRD_PERSON:
        actor_description = actor.description
    else:
        raise ValueError(f"Perspective {perspective} is not implemented")

    return f"{actor_description} {attribute_descriptions}"


def describe_static(entity: WorldEntity) -> str:
    # TODO: include attributes
    return entity.description


def describe_entity(
    entity: WorldEntity,
    perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
) -> str:
    if isinstance(entity, Actor):
        return describe_actor(entity, perspective)

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

    return f"{'. '.join(attribute_descriptions)}"
