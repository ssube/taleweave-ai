from logging import getLogger
from random import random
from typing import Dict, List, Optional

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
    match: Dict[str, str]
    chance: float = 1.0
    remove: Optional[List[str]] = None
    set: Optional[Dict[str, str]] = None
    trigger: Optional[List[str]] = None


@dataclass
class LogicTable:
    rules: List[LogicRule]
    labels: Dict[str, Dict[str, LogicLabel]] = Field(default_factory=dict)


with open("./worlds/logic.yaml") as file:
    logic_rules = LogicTable(**load(file, Loader=Loader))
    logic_triggers = {
        rule: [get_plugin_function(trigger) for trigger in rule.trigger]
        for rule in logic_rules.rules
        if rule.trigger
    }


def update_attributes(
    entity: Room | Actor | Item,
    attributes: Dict[str, str],
    dataset: LogicTable,
) -> Dict[str, str]:
    for rule in dataset.rules:
        if rule.match.items() <= attributes.items():
            logger.info("matched logic: %s", rule.match)
            if rule.chance < 1:
                if random() > rule.chance:
                    logger.info("logic skipped by chance: %s", rule.chance)
                    continue

            if rule.set:
                attributes.update(rule.set)
                logger.info("logic set state: %s", rule.set)

            for key in rule.remove or []:
                attributes.pop(key, None)

            if rule in logic_triggers:
                for trigger in logic_triggers[rule]:
                    attributes = trigger(entity, attributes)

    return attributes


def update_logic(world: World, step: int) -> None:
    for room in world.rooms:
        room.attributes = update_attributes(room, room.attributes, logic_rules)
        for actor in room.actors:
            actor.attributes = update_attributes(actor, actor.attributes, logic_rules)
            for item in actor.items:
                item.attributes = update_attributes(item, item.attributes, logic_rules)
        for item in room.items:
            item.attributes = update_attributes(item, item.attributes, logic_rules)

    logger.info("updated world attributes")


def format_logic(attributes: Dict[str, str], self=True) -> str:
    labels = []

    for attribute, value in attributes.items():
        if attribute in logic_rules.labels and value in logic_rules.labels[attribute]:
            label = logic_rules.labels[attribute][value]
            if self:
                labels.append(label.backstory)
            else:
                labels.append(label.description)

    if len(labels) > 0:
        logger.info("adding labels: %s", labels)

    return " ".join(labels)


def init():
    logger.info("initialized logic system")
    return (update_logic, format_logic)
