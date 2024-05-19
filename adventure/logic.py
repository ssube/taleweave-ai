from functools import partial, wraps
from logging import getLogger
from random import random
from typing import Callable, Dict, List, Optional

from pydantic import Field
from rule_engine import Rule
from yaml import Loader, load

from adventure.game_system import FormatPerspective, GameSystem
from adventure.models.entity import Attributes, World, WorldEntity, dataclass
from adventure.plugins import get_plugin_function

logger = getLogger(__name__)


@dataclass
class LogicLabel:
    backstory: str
    description: str | None = None
    match: Optional[Attributes] = None
    rule: Optional[str] = None


@dataclass
class LogicRule:
    chance: float = 1.0
    group: Optional[str] = None
    match: Optional[Attributes] = None
    remove: Optional[List[str]] = None
    rule: Optional[str] = None
    set: Optional[Attributes] = None
    trigger: Optional[List[str]] = None


@dataclass
class LogicTable:
    rules: List[LogicRule] = Field(default_factory=list)
    labels: List[LogicLabel] = Field(default_factory=list)


LogicTrigger = Callable[[WorldEntity], None]
TriggerTable = Dict[str, LogicTrigger]


def match_logic(
    entity: WorldEntity,
    matcher: LogicLabel | LogicRule,
) -> bool:
    typed_attributes = {
        **entity.attributes,
        "type": entity.type,
    }

    if matcher.rule:
        # TODO: pre-compile rules
        rule_impl = Rule(matcher.rule)
        if not rule_impl.matches(
            {
                "attributes": typed_attributes,
            }
        ):
            logger.debug("logic rule did not match attributes: %s", matcher.rule)
            return False

    if matcher.match and not (matcher.match.items() <= typed_attributes.items()):
        logger.debug("logic did not match attributes: %s", matcher.match)
        return False

    return True


def update_attributes(
    entity: WorldEntity,
    rules: LogicTable,
    triggers: TriggerTable,
) -> None:
    skip_groups = set()

    for rule in rules.rules:
        if rule.group:
            if rule.group in skip_groups:
                logger.debug("already ran a rule from group %s, skipping", rule.group)
                continue

        if not match_logic(entity, rule):
            continue

        logger.info("matched logic: %s", rule.match)
        if rule.chance < 1:
            if random() > rule.chance:
                logger.info("logic skipped by chance: %s", rule.chance)
                continue

        if rule.group:
            skip_groups.add(rule.group)

        for key in rule.remove or []:
            entity.attributes.pop(key, None)

        if rule.set:
            entity.attributes.update(rule.set)
            logger.info("logic set state: %s", rule.set)

        if rule.trigger:
            for trigger in rule.trigger:
                if trigger in triggers:
                    triggers[trigger](entity)


def update_logic(
    world: World, step: int, rules: LogicTable, triggers: TriggerTable
) -> None:
    for room in world.rooms:
        update_attributes(room, rules=rules, triggers=triggers)
        for actor in room.actors:
            update_attributes(actor, rules=rules, triggers=triggers)
            for item in actor.items:
                update_attributes(item, rules=rules, triggers=triggers)
        for item in room.items:
            update_attributes(item, rules=rules, triggers=triggers)

    logger.info("updated world attributes")


def format_logic(
    entity: WorldEntity,
    rules: LogicTable,
    perspective: FormatPerspective = FormatPerspective.SECOND_PERSON,
) -> str:
    labels = []

    for label in rules.labels:
        if match_logic(entity, label):
            if perspective == FormatPerspective.SECOND_PERSON:
                labels.append(label.backstory)
            elif perspective == FormatPerspective.THIRD_PERSON and label.description:
                labels.append(label.description)
            else:
                logger.debug("label has no relevant description: %s", label)

    if len(labels) > 0:
        logger.debug("adding attribute labels: %s", labels)

    return " ".join(labels)


def load_logic(filename: str):
    logger.info("loading logic from file: %s", filename)
    with open(filename) as file:
        logic_rules = LogicTable(**load(file, Loader=Loader))
        logic_triggers = {}

        for rule in logic_rules.rules:
            if rule.trigger:
                for trigger in rule.trigger:
                    logic_triggers[trigger] = get_plugin_function(trigger)

    logger.info("initialized logic system")
    system_simulate = wraps(update_logic)(
        partial(update_logic, rules=logic_rules, triggers=logic_triggers)
    )
    system_format = wraps(format_logic)(partial(format_logic, rules=logic_rules))

    return GameSystem(
        format=system_format,
        simulate=system_simulate,
    )
