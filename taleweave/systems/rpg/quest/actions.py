from taleweave.context import action_context, get_system_data
from taleweave.errors import ActionError
from taleweave.utils.search import find_character_in_room
from taleweave.utils.template import format_prompt

from .system import (
    QUEST_SYSTEM,
    complete_quest,
    get_active_quest,
    get_quests_for_character,
    set_active_quest,
)


def accept_quest(character: str, quest: str) -> str:
    """
    Accept and start a quest being given by another character.
    """

    with action_context() as (action_room, action_character):
        quests = get_system_data(QUEST_SYSTEM)
        if not quests:
            raise ActionError(
                format_prompt("action_accept_quest_error_none", character=character)
            )

        target_character = find_character_in_room(action_room, character)
        if not target_character:
            raise ActionError(
                format_prompt("action_accept_quest_error_room", character=character)
            )

        available_quests = get_quests_for_character(quests, target_character)

        for available_quest in available_quests:
            if available_quest.name == quest:
                set_active_quest(quests, action_character, available_quest)
                return format_prompt(
                    "action_accept_quest_result", character=character, quest=quest
                )

        raise ActionError(
            format_prompt(
                "action_accept_quest_error_name", character=character, quest=quest
            )
        )


def submit_quest(character: str) -> str:
    """
    Submit your active quest to the quest giver. If you have completed the quest, you will be rewarded.
    """

    with action_context() as (action_room, action_character):
        quests = get_system_data(QUEST_SYSTEM)
        if not quests:
            raise ActionError(
                format_prompt("action_submit_quest_error_none", character=character)
            )

        active_quest = get_active_quest(quests, action_character)
        if not active_quest:
            raise ActionError(
                format_prompt("action_submit_quest_error_active", character=character)
            )

        target_character = find_character_in_room(action_room, character)
        if not target_character:
            raise ActionError(
                format_prompt("action_submit_quest_error_room", character=character)
            )

        if active_quest.giver.character == target_character.name:
            complete_quest(quests, action_character, active_quest)
            return format_prompt(
                "action_submit_quest_result",
                character=character,
                quest=active_quest,
            )

        return format_prompt(
            "action_submit_quest_error_name",
            character=character,
            quest=active_quest,
        )
