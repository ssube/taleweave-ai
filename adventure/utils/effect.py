from logging import getLogger
from typing import List

from adventure.models.effect import (
    BooleanEffectPattern,
    BooleanEffectResult,
    EffectPattern,
    EffectResult,
    FloatEffectPattern,
    FloatEffectResult,
    IntEffectPattern,
    IntEffectResult,
    StringEffectPattern,
    StringEffectResult,
)
from adventure.models.entity import Actor, Attributes
from adventure.utils.attribute import (
    add_value,
    append_value,
    multiply_value,
    prepend_value,
)

from .random import resolve_float_range, resolve_int_range, resolve_string_list

logger = getLogger(__name__)


def effective_boolean(attributes: Attributes, effect: BooleanEffectResult) -> bool:
    """
    Apply a boolean effect to a value.
    """

    if effect.set is not None:
        return effect.set

    value = attributes.get(effect.name, False)

    if effect.toggle is not None:
        return not value

    return bool(value)


def effective_float(attributes: Attributes, effect: FloatEffectResult) -> float:
    """
    Apply a float effect to a value.
    """

    if effect.set is not None:
        return effect.set

    value = attributes.get(effect.name, 0.0)

    if effect.offset is not None:
        value = add_value(value, effect.offset)

    if effect.multiply is not None:
        value = multiply_value(value, effect.multiply)

    return float(value)


def effective_int(attributes: Attributes, effect: IntEffectResult) -> int:
    """
    Apply an integer effect to a value.
    """

    if effect.set is not None:
        return effect.set

    value = attributes.get(effect.name, 0)

    if effect.offset is not None:
        value = add_value(value, effect.offset)

    if effect.multiply is not None:
        value = multiply_value(value, effect.multiply)

    return int(value)


def effective_string(attributes: Attributes, effect: StringEffectResult) -> str:
    """
    Apply a string effect to a value.
    """

    if effect.set:
        return effect.set

    value = attributes.get(effect.name, "")

    if effect.append:
        value = append_value(value, effect.append)

    if effect.prepend:
        value = prepend_value(value, effect.prepend)

    return str(value)


def effective_attributes(
    effects: List[EffectResult], base_attributes: Attributes
) -> Attributes:
    """
    Apply an effect to a set of attributes.
    """

    attributes = base_attributes.copy()

    for effect in effects:
        for attribute in effect.attributes:
            if isinstance(attribute, BooleanEffectResult):
                attributes[attribute.name] = effective_boolean(attributes, attribute)
            elif isinstance(attribute, FloatEffectResult):
                attributes[attribute.name] = effective_float(attributes, attribute)
            elif isinstance(attribute, IntEffectResult):
                attributes[attribute.name] = effective_int(attributes, attribute)
            elif isinstance(attribute, StringEffectResult):
                attributes[attribute.name] = effective_string(attributes, attribute)
            else:
                raise ValueError(f"Invalid operation: {attribute.operation}")

    return attributes


def resolve_boolean_effect(effect: BooleanEffectPattern) -> BooleanEffectResult:
    """
    Apply a boolean effect pattern to a set of attributes.
    """

    return BooleanEffectResult(
        name=effect.name,
        set=effect.set,
        toggle=effect.toggle,
    )


def resolve_float_effect(effect: FloatEffectPattern) -> FloatEffectResult:
    """
    Apply a float effect pattern to a set of attributes.
    """

    return FloatEffectResult(
        name=effect.name,
        set=resolve_float_range(effect.set),
        offset=resolve_float_range(effect.offset),
        multiply=resolve_float_range(effect.multiply),
    )


def resolve_int_effect(effect: IntEffectPattern) -> IntEffectResult:
    """
    Apply an integer effect pattern to a set of attributes.
    """

    return IntEffectResult(
        name=effect.name,
        set=resolve_int_range(effect.set),
        offset=resolve_int_range(effect.offset),
        multiply=resolve_float_range(effect.multiply),
    )


def resolve_string_effect(effect: StringEffectPattern) -> StringEffectResult:
    """
    Apply a string effect pattern to a set of attributes.
    """

    return StringEffectResult(
        name=effect.name,
        set=resolve_string_list(effect.set),
        append=resolve_string_list(effect.append),
        prepend=resolve_string_list(effect.prepend),
    )


def resolve_effects(effects: List[EffectPattern]) -> List[EffectResult]:
    """
    Generate results for a set of effect patterns, rolling all of the random values.
    """

    results = []

    for effect in effects:
        attributes = []
        for attribute in effect.attributes:
            if isinstance(attribute, BooleanEffectPattern):
                result = resolve_boolean_effect(attribute)
            elif isinstance(attribute, FloatEffectPattern):
                result = resolve_float_effect(attribute)
            elif isinstance(attribute, IntEffectPattern):
                result = resolve_int_effect(attribute)
            elif isinstance(attribute, StringEffectPattern):
                result = resolve_string_effect(attribute)
            else:
                raise ValueError(f"Invalid operation: {attribute.operation}")
            attributes.append(result)

        duration = resolve_int_range(effect.duration)

        result = EffectResult(
            name=effect.name,
            description=effect.description,
            duration=duration,
            attributes=attributes,
        )
        results.append(result)

    return results


def is_active_effect(effect: EffectResult) -> bool:
    """
    Determine if an effect is active.
    """

    return effect.duration is None or effect.duration > 0


def apply_permanent_results(
    attributes: Attributes, effects: List[EffectResult]
) -> Attributes:
    """
    Permanently apply a set of effects to a set of attributes.
    """

    for effect in effects:
        for attribute in effect.attributes:
            if isinstance(attribute, BooleanEffectResult):
                attributes[attribute.name] = effective_boolean(attributes, attribute)
            elif isinstance(attribute, FloatEffectResult):
                attributes[attribute.name] = effective_float(attributes, attribute)
            elif isinstance(attribute, IntEffectResult):
                attributes[attribute.name] = effective_int(attributes, attribute)
            elif isinstance(attribute, StringEffectResult):
                attributes[attribute.name] = effective_string(attributes, attribute)
            else:
                raise ValueError(f"Invalid operation: {attribute.operation}")

    return attributes


def apply_permanent_effects(
    attributes: Attributes, effects: List[EffectPattern]
) -> Attributes:
    """
    Permanently apply a set of effects to a set of attributes.
    """

    results = resolve_effects(effects)
    return apply_permanent_results(attributes, results)


def apply_effects(target: Actor, effects: List[EffectPattern]) -> None:
    """
    Apply a set of effects to an actor and their attributes.
    """

    permanent_effects = [
        effect for effect in effects if effect.application == "permanent"
    ]
    permanent_effects = resolve_effects(permanent_effects)
    target.attributes = apply_permanent_results(target.attributes, permanent_effects)

    temporary_effects = [
        effect for effect in effects if effect.application == "temporary"
    ]
    temporary_effects = resolve_effects(temporary_effects)
    target.active_effects.extend(temporary_effects)


def expire_effects(target: Actor) -> None:
    """
    Decrement the duration of effects on an actor and remove any that have expired.
    """

    for effect in target.active_effects:
        if effect.duration is not None:
            effect.duration -= 1

    target.active_effects[:] = [
        effect for effect in target.active_effects if is_active_effect(effect)
    ]
