from typing import Dict, Tuple

from packit.agent import Agent

from adventure.models import Actor

current_world = None
current_room = None
current_actor = None
current_step = 0


# TODO: where should this one go?
actor_agents: Dict[str, Tuple[Actor, Agent]] = {}


def get_current_context():
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


def get_current_world():
    return current_world


def get_current_room():
    return current_room


def get_current_actor():
    return current_actor


def set_current_world(world):
    global current_world
    current_world = world


def set_current_room(room):
    global current_room
    current_room = room


def set_current_actor(actor):
    global current_actor
    current_actor = actor


def get_step():
    return current_step


def set_step(step):
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
