from adventure.context import action_context, get_system_data
from adventure.systems.quest import (
    QUEST_SYSTEM,
    complete_quest,
    get_active_quest,
    get_quests_for_character,
    set_active_quest,
)
from adventure.utils.search import find_character_in_room


def accept_quest(character: str, quest: str) -> str:
    """
    Accept and start a quest being given by another character.
    """

    with action_context() as (action_room, action_character):
        quests = get_system_data(QUEST_SYSTEM)
        if not quests:
            return "No quests available."

        target_character = find_character_in_room(action_room, character)
        if not target_character:
            return f"{character} is not in the room."

        available_quests = get_quests_for_character(quests, target_character)

        for available_quest in available_quests:
            if available_quest.name == quest:
                set_active_quest(quests, action_character, available_quest)
                return f"You have accepted the quest: {quest}"

        return f"{character} does not have the quest: {quest}"


def submit_quest(character: str) -> str:
    """
    Submit your active quest to the quest giver. If you have completed the quest, you will be rewarded.
    """

    with action_context() as (action_room, action_character):
        quests = get_system_data(QUEST_SYSTEM)
        if not quests:
            return "No quests available."

        active_quest = get_active_quest(quests, action_character)
        if not active_quest:
            return "You do not have an active quest."

        target_character = find_character_in_room(action_room, character)
        if not target_character:
            return f"{character} is not in the room."

        if active_quest.giver.character == target_character.name:
            complete_quest(quests, action_character, active_quest)
            return f"You have completed the quest: {active_quest.name}"

        return f"{character} is not the quest giver for your active quest."
