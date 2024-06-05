from logging import getLogger

from jinja2 import Environment

from taleweave.context import get_prompt_library

# from taleweave.utils.conversation import summarize_room
from taleweave.utils.string import and_list, or_list
from taleweave.utils.world import describe_entity, name_entity

logger = getLogger(__name__)

jinja_env = Environment()
jinja_env.filters["describe"] = describe_entity
jinja_env.filters["name"] = name_entity
# jinja_env.filters["summary"] = summarize_room
jinja_env.filters["and_list"] = and_list
jinja_env.filters["or_list"] = or_list


def format_prompt(prompt_key: str, **kwargs) -> str:
    try:
        library = get_prompt_library()
        template_str = library.prompts[prompt_key]
        return format_str(template_str, **kwargs)
    except Exception as e:
        logger.exception("error formatting prompt: %s", prompt_key)
        raise e


def format_str(template_str: str, **kwargs) -> str:
    template = jinja_env.from_string(template_str)
    return template.render(**kwargs)
