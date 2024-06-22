from logging import getLogger
from random import randint

from taleweave.context import get_current_world
from taleweave.models.entity import Character, WorldEntity
from taleweave.utils.attribute import subtract_attribute
from taleweave.utils.search import find_containing_room

logger = getLogger(__name__)


def character_bleeding(entity: WorldEntity) -> None:
    world = get_current_world()
    if not world:
        raise ValueError("no world found")

    if not isinstance(entity, Character):
        raise ValueError("bleeding entity must be a character")

    # remove bleeding from health, then reduce bleeding
    amount = int(entity.attributes.get("bleeding", 0))
    subtract_attribute(entity.attributes, "health", amount)

    if amount > 0 and randint(0, 1):
        subtract_attribute(entity.attributes, "bleeding", 1)

    # leave blood in the room
    room = find_containing_room(world, entity)
    if room:
        room.attributes["bloody"] = True
        logger.info(f"{entity.name} bleeds in {room.name}")
    else:
        logger.warning(f"{entity.name} not found in any room")
