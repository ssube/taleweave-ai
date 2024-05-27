import random
from typing import List

from taleweave.models.base import FloatRange, IntRange


def resolve_float_range(range: float | FloatRange | None) -> float | None:
    """
    Resolve a float range to a single value.
    """

    if range is None:
        return None

    if isinstance(
        range, (float, int)
    ):  # int is not really necessary here, but mypy complains without it
        return range

    return random.uniform(range.min, range.max)


def resolve_int_range(range: int | IntRange | None) -> int | None:
    """
    Resolve an integer range to a single value.
    """

    if range is None:
        return None

    if isinstance(range, int):
        return range

    return random.randint(range.min, range.max)


def resolve_string_list(result: str | List[str] | None) -> str | None:
    """
    Resolve a string result to a single value.
    """

    if result is None:
        return None

    if isinstance(result, str):
        return result

    return random.choice(result)
