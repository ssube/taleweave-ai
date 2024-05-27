from collections import deque
from json import dump
from os import path
from typing import Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from packit.agent import Agent, agent_easy_connect
from pydantic import RootModel

from adventure.context import get_all_character_agents, set_character_agent
from adventure.models.entity import World
from adventure.player import LocalPlayer

MEMORY_LIMIT = 25  # 10


def create_agents(
    world: World,
    memory: Dict[str, List[str | Dict[str, str]]] = {},
    players: List[str] = [],
):
    # set up agents for each character
    llm = agent_easy_connect()

    for room in world.rooms:
        for character in room.characters:
            if character.name in players:
                agent = LocalPlayer(character.name, character.backstory)
                agent_memory = restore_memory(memory.get(character.name, []))
                agent.load_history(agent_memory)
            else:
                agent = Agent(character.name, character.backstory, {}, llm)
                agent.memory = restore_memory(memory.get(character.name, []))
            set_character_agent(character.name, character, agent)


def graph_world(world: World, turn: int):
    import graphviz

    graph_name = f"{path.basename(world.name)}-{turn}"
    graph = graphviz.Digraph(graph_name, format="png")
    for room in world.rooms:
        characters = [character.name for character in room.characters]
        room_label = "\n".join([room.name, *characters])
        graph.node(room.name, room_label)
        for portal in room.portals:
            graph.edge(room.name, portal.destination, label=portal.name)

    graph_path = path.dirname(world.name)
    graph.render(directory=graph_path)


def snapshot_world(world: World, turn: int):
    # save the world itself, along with the turn number and the memory of each agent
    json_world = RootModel[World](world).model_dump()

    json_memory = {}

    for character, agent in get_all_character_agents():
        json_memory[character.name] = list(agent.memory or [])

    return {
        "world": json_world,
        "memory": json_memory,
        "turn": turn,
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

    return deque(memories, maxlen=MEMORY_LIMIT)


def save_world(world, filename):
    with open(filename, "w") as f:
        json_world = RootModel[World](world).model_dump_json(indent=2)
        f.write(json_world)


def save_world_state(world, turn, filename):
    graph_world(world, turn)
    json_state = snapshot_world(world, turn)
    with open(filename, "w") as f:
        dump(json_state, f, default=world_json, indent=2)


def world_json(obj):
    if isinstance(obj, BaseMessage):
        return {
            "content": obj.content,
            "type": obj.type,
        }

    raise ValueError(f"Cannot serialize {obj}")
