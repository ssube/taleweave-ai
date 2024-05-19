from collections import deque
from json import dump
from os import path
from typing import Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from packit.agent import Agent, agent_easy_connect
from pydantic import RootModel

from adventure.context import get_all_actor_agents, set_actor_agent
from adventure.models.entity import World
from adventure.player import LocalPlayer


def create_agents(
    world: World,
    memory: Dict[str, List[str | Dict[str, str]]] = {},
    players: List[str] = [],
):
    # set up agents for each actor
    llm = agent_easy_connect()

    for room in world.rooms:
        for actor in room.actors:
            if actor.name in players:
                agent = LocalPlayer(actor.name, actor.backstory)
                agent_memory = restore_memory(memory.get(actor.name, []))
                agent.load_history(agent_memory)
            else:
                agent = Agent(actor.name, actor.backstory, {}, llm)
                agent.memory = restore_memory(memory.get(actor.name, []))
            set_actor_agent(actor.name, actor, agent)


def graph_world(world: World, step: int):
    import graphviz

    graph_name = f"{path.basename(world.name)}-{step}"
    graph = graphviz.Digraph(graph_name, format="png")
    for room in world.rooms:
        room_label = "\n".join([room.name, *[actor.name for actor in room.actors]])
        graph.node(room.name, room_label)
        for portal in room.portals:
            graph.edge(room.name, portal.destination, label=portal.name)

    graph_path = path.dirname(world.name)
    graph.render(directory=graph_path)


def snapshot_world(world: World, step: int):
    # save the world itself, along with the step number of the memory of each agent
    json_world = RootModel[World](world).model_dump()

    json_memory = {}

    for actor, agent in get_all_actor_agents():
        json_memory[actor.name] = list(agent.memory or [])

    return {
        "world": json_world,
        "memory": json_memory,
        "step": step,
    }


def restore_memory(
    data: Sequence[str | Dict[str, str]]
) -> deque[str | AIMessage | HumanMessage | SystemMessage]:
    memories = []

    for memory in data:
        if isinstance(memory, str):
            memories.append(memory)
        elif isinstance(memory, dict):
            memory_content = memory["content"]
            memory_type = memory["type"]

            if memory_type == "human":
                memories.append(HumanMessage(content=memory_content))
            elif memory_type == "system":
                memories.append(SystemMessage(content=memory_content))
            elif memory_type == "ai":
                memories.append(AIMessage(content=memory_content))

    return deque(memories, maxlen=10)


def save_world(world, filename):
    with open(filename, "w") as f:
        json_world = RootModel[World](world).model_dump_json(indent=2)
        f.write(json_world)


def save_world_state(world, step, filename):
    graph_world(world, step)
    json_state = snapshot_world(world, step)
    with open(filename, "w") as f:
        dump(json_state, f, default=world_json, indent=2)


def world_json(obj):
    if isinstance(obj, BaseMessage):
        return {
            "content": obj.content,
            "type": obj.type,
        }

    raise ValueError(f"Cannot serialize {obj}")
