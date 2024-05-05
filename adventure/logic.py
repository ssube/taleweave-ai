from logging import getLogger
from random import random
from typing import Callable, Dict, List, Optional
from functools import partial

from rule_engine import Rule
from pydantic import Field
from yaml import Loader, load

from adventure.models import Actor, Item, Room, World, dataclass
from adventure.plugins import get_plugin_function

logger = getLogger(__name__)


@dataclass
class LogicLabel:
    backstory: str
    description: str


@dataclass
class LogicRule:
    chance: float = 1.0
    group: Optional[str] = None
    match: Optional[Dict[str, str]] = None
    remove: Optional[List[str]] = None
    rule: Optional[str] = None
    set: Optional[Dict[str, str]] = None
    trigger: Optional[List[str]] = None


@dataclass
class LogicTable:
    rules: List[LogicRule]
    labels: Dict[str, Dict[str, LogicLabel]] = Field(default_factory=dict)


LogicTrigger = Callable[[Room | Actor | Item, Dict[str, str]], Dict[str, str]]
TriggerTable = Dict[LogicRule, List[LogicTrigger]]


def update_attributes(
    entity: Room | Actor | Item,
    attributes: Dict[str, str],
    rules: LogicTable,
    triggers: TriggerTable,
) -> Dict[str, str]:
    entity_type = entity.__class__.__name__.lower()
    skip_groups = set()

    for rule in rules.rules:
        if rule.group:
            if rule.group in skip_groups:
                logger.debug("skipping logic group: %s", rule.group)
                continue

            skip_groups.add(rule.group)

        typed_attributes = {
            **attributes,
            "type": entity_type,
        }

        if rule.rule:
            # TODO: pre-compile rules
            rule_impl = Rule(rule.rule)
            if not rule_impl.matches({
                "attributes": typed_attributes,
            }):
                logger.debug("logic rule did not match attributes: %s", rule.rule)
                continue

        if rule.match and not(rule.match.items() <= typed_attributes.items()):
            logger.debug("logic did not match attributes: %s", rule.match)
            continue

        logger.info("matched logic: %s", rule.match)
        if rule.chance < 1:
            if random() > rule.chance:
                logger.info("logic skipped by chance: %s", rule.chance)
                continue

        for key in rule.remove or []:
            attributes.pop(key, None)

        if rule.set:
            attributes.update(rule.set)
            logger.info("logic set state: %s", rule.set)

        if rule in triggers:
            for trigger in triggers[rule]:
                attributes = trigger(entity, attributes)

    return attributes


def update_logic(world: World, step: int, rules: LogicTable, triggers: TriggerTable) -> None:
    for room in world.rooms:
        room.attributes = update_attributes(room, room.attributes, rules=rules, triggers=triggers)
        for actor in room.actors:
            actor.attributes = update_attributes(actor, actor.attributes, rules=rules, triggers=triggers)
            for item in actor.items:
                item.attributes = update_attributes(item, item.attributes, rules=rules, triggers=triggers)
        for item in room.items:
            item.attributes = update_attributes(item, item.attributes, rules=rules, triggers=triggers)

    logger.info("updated world attributes")


def format_logic(attributes: Dict[str, str], rules: LogicTable, self=True) -> str:
    labels = []

    for attribute, value in attributes.items():
        if attribute in rules.labels and value in rules.labels[attribute]:
            label = rules.labels[attribute][value]
            if self:
                labels.append(label.backstory)
            else:
                labels.append(label.description)

    if len(labels) > 0:
        logger.info("adding labels: %s", labels)

    return " ".join(labels)


def init_from_file(filename: str):
    logger.info("loading logic from file: %s", filename)
    with open(filename) as file:
        logic_rules = LogicTable(**load(file, Loader=Loader))
        logic_triggers = {
            rule: [get_plugin_function(trigger) for trigger in rule.trigger]
            for rule in logic_rules.rules
            if rule.trigger
        }

    logger.info("initialized logic system")
    return (
        partial(update_logic, rules=logic_rules, triggers=logic_triggers),
        partial(format_logic, rules=logic_rules)
    )
