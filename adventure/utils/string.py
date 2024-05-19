from functools import lru_cache


@lru_cache(maxsize=1024)
def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = name.strip('"').strip("'")
    return name.removesuffix(".")
