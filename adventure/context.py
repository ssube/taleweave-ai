from typing import Callable, Dict, Tuple

from packit.agent import Agent

from adventure.models import Actor, Room, World

current_broadcast: Callable[[str], None] | None = None
current_world: World | None = None
current_room: Room | None = None
current_actor: Actor | None = None
current_step = 0
dungeon_master: Agent | None = None


# TODO: where should this one go?
actor_agents: Dict[str, Tuple[Actor, Agent]] = {}


def get_current_context() -> Tuple[World, Room, Actor]:
    if not current_world:
        raise ValueError(
            "The current world must be set before calling action functions"
        )
    if not current_room:
        raise ValueError("The current room must be set before calling action functions")
    if not current_actor:
        raise ValueError(
            "The current actor must be set before calling action functions"
        )

    return (current_world, current_room, current_actor)


def get_current_world() -> World | None:
    return current_world


def get_current_room() -> Room | None:
    return current_room


def get_current_actor() -> Actor | None:
    return current_actor


def get_current_broadcast():
    return current_broadcast


def broadcast(message: str):
    if current_broadcast:
        current_broadcast(message)


def set_current_broadcast(broadcast):
    global current_broadcast
    current_broadcast = broadcast


def set_current_world(world: World | None):
    global current_world
    current_world = world


def set_current_room(room: Room | None):
    global current_room
    current_room = room


def set_current_actor(actor: Actor | None):
    global current_actor
    current_actor = actor


def get_current_step() -> int:
    return current_step


def set_current_step(step: int):
    global current_step
    current_step = step


def get_actor_for_agent(agent):
    return next(
        (
            inner_actor
            for inner_actor, inner_agent in actor_agents.values()
            if inner_agent == agent
        ),
        None,
    )


def get_agent_for_actor(actor):
    return next(
        (
            inner_agent
            for inner_actor, inner_agent in actor_agents.values()
            if inner_actor == actor
        ),
        None,
    )


def get_actor_agent_for_name(name):
    return next(
        (
            (actor, agent)
            for actor, agent in actor_agents.values()
            if actor.name == name
        ),
        (None, None),
    )


def set_actor_agent_for_name(name, actor, agent):
    actor_agents[name] = (actor, agent)


def get_all_actor_agents():
    return list(actor_agents.values())


def set_dungeon_master(agent):
    global dungeon_master
    dungeon_master = agent


def get_dungeon_master() -> Agent:
    if not dungeon_master:
        raise ValueError(
            "The dungeon master must be set before calling action functions"
        )

    return dungeon_master
