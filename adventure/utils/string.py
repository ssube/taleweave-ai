from functools import lru_cache
from typing import List


@lru_cache(maxsize=1024)
def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = name.strip('"').strip("'")
    return name.removesuffix(".")


def and_list(items: List[str]) -> str:
    """
    Convert a list of items into a human-readable list.
    """
    if not items:
        return "nothing"

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def or_list(items: List[str]) -> str:
    """
    Convert a list of items into a human-readable list.
    """
    if not items:
        return "nothing"

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])}, or {items[-1]}"
