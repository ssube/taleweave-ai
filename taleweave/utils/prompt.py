from logging import getLogger

from jinja2 import Environment

from taleweave.context import get_prompt_library
from taleweave.utils.world import describe_entity, name_entity

logger = getLogger(__name__)


def format_prompt(prompt_key: str, **kwargs) -> str:
    try:
        library = get_prompt_library()
        template_str = library.prompts[prompt_key]
        return format_str(template_str, **kwargs)
    except Exception as e:
        logger.exception("error formatting prompt: %s", prompt_key)
        raise e


def format_str(template_str: str, **kwargs) -> str:
    env = Environment()
    env.filters["describe"] = describe_entity
    env.filters["name"] = name_entity

    template = env.from_string(template_str)
    return template.render(**kwargs)