from typing import Callable


def try_parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def try_parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def format_callable(fn: Callable | None) -> str:
    if fn:
        return f"{fn.__module__}:{fn.__name__}"

    return "None"
