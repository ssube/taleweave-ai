from logging import getLogger
from typing import Dict, List, Literal, Optional

from packit.agent import Agent
from pydantic import Field

from taleweave.context import get_system_data
from taleweave.game_system import GameSystem, SystemData
from taleweave.models.base import Attributes, dataclass, uuid
from taleweave.models.entity import (
    Character,
    EntityReference,
    Item,
    Room,
    World,
    WorldEntity,
)
from taleweave.systems.generic.logic import match_logic
from taleweave.utils.search import (
    find_entity_reference,
    find_item_in_container,
    find_item_in_room,
)
from taleweave.utils.systems import load_system_data, save_system_data

logger = getLogger(__name__)


QUEST_SYSTEM = "quest"


# region models
@dataclass
class QuestGoalContains:
    """
    Quest goal for any kind of fetch quest, including delivery and escort quests.

    Valid combinations are:
    - container: Room and items: List[Character | Item]
    - container: Character and items: List[Item]
    """

    container: EntityReference
    contents: List[EntityReference] = Field(default_factory=list)
    type: Literal["contains"] = "contains"


@dataclass
class QuestGoalAttributes:
    """
    Quest goal for any kind of attribute quest, including spell casting and item usage.
    """

    target: EntityReference
    match: Optional[Attributes] = None
    rule: Optional[str] = None
    type: Literal["attributes"] = "attributes"


QuestGoal = QuestGoalAttributes | QuestGoalContains


@dataclass
class QuestReward:
    pass


@dataclass
class Quest:
    name: str
    description: str
    giver: EntityReference
    goal: QuestGoal
    reward: QuestReward
    type: Literal["quest"] = "quest"
    id: str = Field(default_factory=uuid)


@dataclass
class QuestData:
    active: Dict[str, Quest]
    available: Dict[str, List[Quest]]
    completed: Dict[str, List[Quest]]


# endregion


# region state helpers
def complete_quest(quests: QuestData, character: Character, quest: Quest) -> None:
    """
    Complete the given quest for the given character.
    """
    if quest in quests.available.get(character.name, []):
        quests.available[character.name].remove(quest)

    if quest == quests.active.get(character.name, None):
        del quests.active[character.name]

    if character.name not in quests.completed:
        quests.completed[character.name] = []

    quests.completed[character.name].append(quest)


def get_quests_for_character(quests: QuestData, character: Character) -> List[Quest]:
    """
    Get all quests for the given character.
    """
    return quests.available.get(character.name, [])


def set_active_quest(quests: QuestData, character: Character, quest: Quest) -> None:
    """
    Set the active quest for the given character.
    """
    quests.active[character.name] = quest


def get_active_quest(quests: QuestData, character: Character) -> Quest | None:
    """
    Get the active quest for the given character.
    """
    return quests.active.get(character.name)


def is_quest_complete(world: World, quest: Quest) -> bool:
    """
    Check if the given quest is complete.
    """

    if quest.goal.type == "contains":
        container = find_entity_reference(world, quest.goal.container)
        if not container:
            raise ValueError(f"quest container not found: {quest.goal.container}")

        for content in quest.goal.contents:
            if isinstance(container, Room):
                if content.item:
                    if not find_item_in_room(container, content.item):
                        return False
            elif isinstance(container, (Character, Item)):
                if content.item:
                    if not find_item_in_container(container, content.item):
                        return False
            else:
                logger.warning(f"unsupported container type: {container}")
                return False

        return True
    elif quest.goal.type == "attributes":
        target = find_entity_reference(world, quest.goal.target)
        if not target:
            raise ValueError(f"quest target not found: {quest.goal.target}")

        if match_logic(target, quest.goal):
            return True

    return False


# endregion


# region game system callbacks
def initialize_quests(world: World) -> QuestData:
    """
    Initialize quests for the world.
    """

    logger.info("initializing quest data for world %s", world.name)
    return QuestData(active={}, available={}, completed={})


def generate_quests(agent: Agent, world: World, entity: WorldEntity) -> None:
    """
    Generate new quests for the world.
    """

    quests: QuestData | None = get_system_data(QUEST_SYSTEM)
    if not quests:
        raise ValueError("Quest data is required for quest generation")

    if isinstance(entity, Character):
        available_quests = get_quests_for_character(quests, entity)
        if len(available_quests) == 0:
            logger.info(f"generating new quest for {entity.name}")
            # TODO: generate one new quest


def simulate_quests(world: World, turn: int, data: QuestData | None = None) -> None:
    """
    1. Check for any completed quests.
    2. Update any active quests.
    3. Generate any new quests.
    """

    # TODO: switch to using data parameter
    quests: QuestData | None = get_system_data(QUEST_SYSTEM)
    if not quests:
        # TODO: initialize quest data for worlds that don't have it
        raise ValueError("Quest data is required for simulation")

    for room in world.rooms:
        for character in room.characters:
            active_quest = get_active_quest(quests, character)
            if active_quest:
                logger.info(
                    f"simulating quest for {character.name}: {active_quest.name}"
                )
                if is_quest_complete(world, active_quest):
                    logger.info(
                        f"quest complete for {character.name}: {active_quest.name}"
                    )
                    complete_quest(quests, character, active_quest)


# endregion


# region I/O
def load_quest_data(file: str) -> QuestData:
    logger.info(f"loading quest data from {file}")
    return load_system_data(QuestData, file)


def save_quest_data(file: str, data: QuestData) -> None:
    logger.info(f"saving quest data to {file}")
    return save_system_data(QuestData, file, data)


# endregion


def init() -> List[GameSystem]:
    return [
        GameSystem(
            QUEST_SYSTEM,
            data=SystemData(
                load=load_quest_data,
                save=save_quest_data,
            ),
            generate=generate_quests,
            initialize=initialize_quests,
            simulate=simulate_quests,
        )
    ]
