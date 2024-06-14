from logging import getLogger

from jinja2 import Environment

from taleweave.context import get_prompt_library
from taleweave.utils.string import and_list, or_list
from taleweave.utils.world import describe_entity, name_entity

logger = getLogger(__name__)


def a_prefix(name: str) -> str:
    first_word = name.split(" ")[0]
    if first_word.lower() in ["a", "an", "the"]:
        return name

    if name[0].lower() in "aeiou":
        return f"an {name}"

    return f"a {name}"


def the_prefix(name: str) -> str:
    first_word = name.split(" ")[0]
    if first_word.lower() in ["a", "an", "the"]:
        return name

    return f"the {name}"


def punctuate(name: str, suffix: str = ".") -> str:
    if len(name) == 0:
        return name

    if name[-1] in [".", "!", "?", suffix]:
        return name

    return f"{name}{suffix}"


jinja_env = Environment()
jinja_env.filters["describe"] = describe_entity
jinja_env.filters["name"] = name_entity
jinja_env.filters["and_list"] = and_list
jinja_env.filters["or_list"] = or_list
jinja_env.filters["a_prefix"] = a_prefix
jinja_env.filters["the_prefix"] = the_prefix
jinja_env.filters["punctuate"] = punctuate


def format_prompt(prompt_key: str, **kwargs) -> str:
    try:
        library = get_prompt_library()
        template_str = library.prompts[prompt_key]
        return format_str(template_str, **kwargs)
    except Exception as e:
        logger.exception("error formatting prompt: %s", prompt_key)
        raise e


def format_str(template_str: str, **kwargs) -> str:
    """
    Render a template string with the given keyword arguments.

    Jinja will cache the template for future use.
    """
    template = jinja_env.from_string(template_str)
    return template.render(**kwargs)
