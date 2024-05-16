from typing import List

from adventure.models.entity import Attributes, Effect
from adventure.utils.attribute import (
    add_attribute,
    append_attribute,
    divide_attribute,
    multiply_attribute,
    prepend_attribute,
    set_attribute,
    subtract_attribute,
)


def apply_effect(effect: Effect, attributes: Attributes) -> Attributes:
    """
    Apply an effect to a set of attributes.
    """
    for attribute in effect.attributes:
        if attribute.operation == "set":
            set_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "add":
            add_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "subtract":
            subtract_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "multiply":
            multiply_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "divide":
            divide_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "append":
            append_attribute(attributes, attribute.name, attribute.value)
        elif attribute.operation == "prepend":
            prepend_attribute(attributes, attribute.name, attribute.value)
        else:
            raise ValueError(f"Invalid operation: {attribute.operation}")

    return attributes


def apply_effects(effects: List[Effect], attributes: Attributes) -> Attributes:
    """
    Apply a list of effects to a set of attributes.
    """
    for effect in effects:
        attributes = apply_effect(effect, attributes)

    return attributes
