from logging import getLogger
from typing import Callable, List

from packit.agent import Agent, agent_easy_connect

from taleweave.context import (
    action_context,
    add_extra_actions,
    broadcast,
    get_agent_for_character,
    get_current_turn,
    get_dungeon_master,
    get_game_systems,
    has_dungeon_master,
    set_dungeon_master,
    world_context,
)
from taleweave.errors import ActionError
from taleweave.generate import (
    generate_item,
    generate_portals,
    generate_room,
    link_rooms,
)
from taleweave.systems.action import ACTION_SYSTEM_NAME
from taleweave.utils.effect import apply_effects, is_effect_ready
from taleweave.utils.search import find_character_in_room
from taleweave.utils.string import normalize_name
from taleweave.utils.template import format_prompt
from taleweave.utils.world import describe_entity

logger = getLogger(__name__)

# this is the fallback dungeon master if none is set
if not has_dungeon_master():
    llm = agent_easy_connect()
    set_dungeon_master(
        Agent(
            "dungeon master",
            format_prompt("world_default_dungeon_master"),
            {},
            llm,
        )
    )


def action_explore(direction: str) -> str:
    """
    Explore the room in a new direction. You can only explore directions that do not already have a portal.

    Args:
        direction: The direction to explore. For example: inside, outside, upstairs, downstairs, trapdoor, portal, etc.
    """

    with world_context() as (action_world, action_room, action_character):
        dungeon_master = get_dungeon_master()

        if direction in action_room.portals:
            dest_room = action_room.portals[direction]
            raise ActionError(
                format_prompt(
                    "action_explore_error_direction",
                    direction=direction,
                    dest_room=dest_room,
                )
            )

        try:
            systems = get_game_systems()
            new_room = generate_room(dungeon_master, action_world, systems)
            action_world.rooms.append(new_room)

            # link the rooms together, starting with the current room
            outgoing_portal, incoming_portal = generate_portals(
                dungeon_master,
                action_world,
                action_room,
                new_room,
                systems,
                outgoing_name=direction,
            )
            action_room.portals.append(outgoing_portal)
            new_room.portals.append(incoming_portal)
            link_rooms(dungeon_master, action_world, systems, [new_room])

            broadcast(
                format_prompt(
                    "action_explore_broadcast",
                    action_character=action_character,
                    action_room=action_room,
                    direction=direction,
                    new_room=new_room,
                )
            )
            return format_prompt(
                "action_explore_result", direction=direction, new_room=new_room
            )
        except Exception:
            logger.exception("error generating room")
            return format_prompt("action_explore_error_generating", direction=direction)


def action_search(unused: bool) -> str:
    """
    Search the room for hidden items.
    """

    with world_context() as (action_world, action_room, action_character):
        dungeon_master = get_dungeon_master()

        if len(action_room.items) > 2:
            return format_prompt("action_search_error_full")

        try:
            systems = get_game_systems()
            new_item = generate_item(
                dungeon_master,
                action_world,
                systems,
                dest_room=action_room,
            )
            action_room.items.append(new_item)

            broadcast(
                format_prompt(
                    "action_search_broadcast",
                    action_character=action_character,
                    action_room=action_room,
                    new_item=new_item,
                )
            )
            return format_prompt("action_search_result", new_item=new_item)
        except Exception:
            logger.exception("error generating item")
            return format_prompt("action_search_error_generating")


def action_use(item: str, target: str) -> str:
    """
    Use an item on yourself or another character in the room.

    Args:
        item: The name of the item to use.
        target: The name of the character to use the item on, or "self" to use the item on yourself.
    """
    with action_context() as (action_room, action_character):
        dungeon_master = get_dungeon_master()

        action_item = next(
            (
                search_item
                for search_item in (action_character.items + action_room.items)
                if normalize_name(search_item.name) == normalize_name(item)
            ),
            None,
        )
        if not action_item:
            raise ActionError(format_prompt("action_use_error_item", item=item))

        if target == "self":
            target_character = action_character
            target = action_character.name
        else:
            # TODO: allow targeting the room itself and items in the room
            target_character = find_character_in_room(action_room, target)
            if not target_character:
                return format_prompt("action_use_error_target", target=target)

        effect_names = [effect.name for effect in action_item.effects]
        # TODO: should use a retry loop and enum result parser
        chosen_name = dungeon_master(
            format_prompt(
                "action_use_dm_effect",
                action_character=action_character,
                item=item,
                target=target,
                effect_names=effect_names,
            )
        )
        chosen_name = normalize_name(chosen_name)

        effect = next(
            (
                search_effect
                for search_effect in action_item.effects
                if normalize_name(search_effect.name) == chosen_name
            ),
            None,
        )
        if not effect:
            raise ValueError(f"The {chosen_name} effect is not available to apply.")

        current_turn = get_current_turn()
        effect_ready = is_effect_ready(effect, current_turn)

        if effect_ready == "cooldown":
            raise ActionError(
                format_prompt("action_use_error_cooldown", effect=effect, item=item)
            )
        elif effect_ready == "exhausted":
            raise ActionError(
                format_prompt("action_use_error_exhausted", effect=effect, item=item)
            )
        elif effect.uses is not None:
            effect.uses -= 1

        effect.last_used = current_turn

        try:
            apply_effects(target_character, [effect])
        except Exception:
            logger.exception("error applying effect: %s", effect)
            raise ValueError(
                f"There was a problem applying the {chosen_name} effect while using the {item} item."
            )

        broadcast(
            format_prompt(
                "action_use_broadcast_effect",
                action_character=action_character,
                effect=effect,
                item=item,
                target=target,
            )
        )
        outcome = dungeon_master(
            format_prompt(
                "action_use_dm_outcome",
                action_character=action_character,
                action_item=action_item,
                describe_entity=describe_entity,
                effect=effect,
                item=item,
                target_character=target_character,
            )
        )
        broadcast(
            format_prompt(
                "action_use_broadcast_outcome",
                action_character=action_character,
                action_item=action_item,
                effect=effect,
                item=item,
                target=target,
                outcome=outcome,
            )
        )

        # make sure both agents remember the outcome
        target_agent = get_agent_for_character(target_character)
        if target_agent and target_agent.memory:
            target_agent.memory.append(outcome)

        return outcome


def init_optional() -> List[Callable]:
    """
    Initialize the custom actions.
    """
    return add_extra_actions(
        ACTION_SYSTEM_NAME,
        [
            action_explore,
            action_search,
            action_use,
        ],
    )
