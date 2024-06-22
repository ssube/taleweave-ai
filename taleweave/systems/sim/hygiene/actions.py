from taleweave.context import action_context, get_dungeon_master
from taleweave.utils.world import describe_entity


def action_wash(unused: bool) -> str:
    """
    Wash yourself.
    """

    with action_context() as (action_room, action_character):
        hygiene = action_character.attributes.get("hygiene", "clean")

        dungeon_master = get_dungeon_master()
        outcome = dungeon_master(
            f"{action_character.name} washes themselves in the {action_room.name}. "
            f"{describe_entity(action_room)}. {describe_entity(action_character)}"
            f"{action_character.name} was {hygiene} to start with. How clean are they after washing? Respond with 'clean' or 'dirty'."
            "If the room has a shower or running water, they should be cleaner. If the room is dirty, they should end up dirtier."
        )

        action_character.attributes["clean"] = outcome.strip().lower()
        return f"You wash yourself in the {action_room.name} and feel {outcome}"
