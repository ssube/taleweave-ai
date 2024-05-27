from functools import partial, wraps
from logging import getLogger
from os import path
from random import random
from typing import Any, Dict, List, Optional, Protocol

from pydantic import Field
from rule_engine import Rule
from yaml import Loader, load

from taleweave.game_system import FormatPerspective, GameSystem
from taleweave.models.entity import Attributes, World, WorldEntity, dataclass
from taleweave.plugins import get_plugin_function

logger = getLogger(__name__)


@dataclass
class LogicLabel:
    backstory: str | None = None
    description: str | None = None
    match: Optional[Attributes] = None
    rule: Optional[str] = None


@dataclass
class LogicRuleTrigger:
    function: str
    parameters: Optional[Attributes] = Field(default_factory=dict)


@dataclass
class LogicRule:
    chance: float = 1.0
    group: Optional[str] = None
    match: Optional[Attributes] = None
    remove: Optional[List[str]] = None
    rule: Optional[str] = None
    set: Optional[Attributes] = None
    trigger: Optional[List[str | LogicRuleTrigger]] = None


@dataclass
class LogicTable:
    rules: List[LogicRule] = Field(default_factory=list)
    labels: List[LogicLabel] = Field(default_factory=list)


class LogicTrigger(Protocol):
    def __call__(self, entity: WorldEntity, **kwargs):
        # comment to keep lint from combining this with the next line
        ...


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
                if isinstance(trigger, str):
                    trigger_name = trigger
                    trigger_params: Attributes = {}
                else:
                    trigger_name = trigger.function
                    trigger_params = trigger.parameters or {}

                if trigger_name in triggers:
                    trigger_function = triggers[trigger_name]
                    trigger_function(entity, **trigger_params)


def update_logic(
    world: World,
    turn: int,
    data: Any | None = None,
    *,
    rules: LogicTable,
    triggers: TriggerTable,
) -> None:
    for room in world.rooms:
        update_attributes(room, rules=rules, triggers=triggers)
        for character in room.characters:
            update_attributes(character, rules=rules, triggers=triggers)
            for item in character.items:
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
            if perspective == FormatPerspective.SECOND_PERSON and label.backstory:
                labels.append(label.backstory)
            elif perspective == FormatPerspective.THIRD_PERSON and label.description:
                labels.append(label.description)
            else:
                logger.debug("label has no relevant description: %s", label)

    if len(labels) > 0:
        logger.debug("adding attribute labels: %s", labels)

    return " ".join(labels)


def load_logic(filename: str):
    basename = path.splitext(path.basename(filename))[0]
    system_name = f"logic_{basename}"
    logger.info("loading logic from file %s as system %s", filename, system_name)

    with open(filename) as file:
        logic_rules = LogicTable(**load(file, Loader=Loader))
        logic_triggers = {}

        for rule in logic_rules.rules:
            if rule.trigger:
                for trigger in rule.trigger:
                    function_name = (
                        trigger if isinstance(trigger, str) else trigger.function
                    )
                    logic_triggers[trigger] = get_plugin_function(function_name)

    logger.info("initialized logic system")
    system_format = wraps(format_logic)(partial(format_logic, rules=logic_rules))
    system_initialize = wraps(update_logic)(
        partial(update_logic, turn=0, rules=logic_rules, triggers=logic_triggers)
    )
    system_simulate = wraps(update_logic)(
        partial(update_logic, rules=logic_rules, triggers=logic_triggers)
    )

    return GameSystem(
        name=system_name,
        format=system_format,
        initialize=system_initialize,
        simulate=system_simulate,
    )
