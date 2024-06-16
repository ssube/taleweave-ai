from functools import partial
from itertools import count
from logging import getLogger
from os import path
from typing import List

from packit.agent import Agent, agent_easy_connect
from packit.memory import make_limited_memory

from taleweave.context import (
    get_current_turn,
    get_system_data,
    set_current_turn,
    set_dungeon_master,
    set_system_data,
)
from taleweave.game_system import GameSystem
from taleweave.generate import generate_room, generate_world, link_rooms
from taleweave.models.config import Config
from taleweave.models.entity import World, WorldState
from taleweave.models.files import WorldPrompt
from taleweave.state import create_agents, save_world
from taleweave.utils.file import load_yaml
from taleweave.utils.template import format_prompt

logger = getLogger(__name__)


def load_or_initialize_system_data(
    world_path: str, systems: List[GameSystem], world: World
):
    for system in systems:
        if system.data:
            system_data_file = f"{world_path}.{system.name}.json"

            if path.exists(system_data_file):
                logger.info(f"loading system data from {system_data_file}")
                data = system.data.load(system_data_file)
                set_system_data(system.name, data)
                continue
            else:
                logger.info(f"no system data found at {system_data_file}")

        if system.initialize:
            logger.info(f"initializing system data for {system.name}")
            data = system.initialize(world)
            set_system_data(system.name, data)


def save_system_data(world_path: str, systems: List[GameSystem]):
    for system in systems:
        if system.data:
            system_data_file = f"{world_path}.{system.name}.json"
            logger.info(f"saving system data to {system_data_file}")
            system.data.save(system_data_file, get_system_data(system.name))


def load_or_generate_world(
    world_path: str,
    state_path: str | None,
    config: Config,
    players,  # TODO: type me
    systems: List[GameSystem],
    world_prompt: WorldPrompt,
    add_rooms: int = 0,
    room_count: int | None = None,
):
    world_file = world_path + ".json"
    world_state_file = state_path or (world_path + ".state.json")

    memory = {}
    turn = 0

    # prepare an agent for the world builder
    llm = agent_easy_connect()
    memory_factory = partial(
        make_limited_memory, limit=config.world.character.memory_limit
    )
    world_builder = Agent(
        "World Builder",
        format_prompt(
            "world_generate_dungeon_master",
            flavor=world_prompt.flavor,
            theme=world_prompt.theme,
        ),
        {},
        llm,
        memory_factory=memory_factory,
    )
    set_dungeon_master(world_builder)

    if path.exists(world_state_file):
        logger.info(f"loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load_yaml(f))

        set_current_turn(state.turn)
        load_or_initialize_system_data(world_path, systems, state.world)

        memory = state.memory
        turn = state.turn
        world = state.world
    elif path.exists(world_file):
        logger.info(f"loading world from {world_file}")
        with open(world_file, "r") as f:
            world = World(**load_yaml(f))

        load_or_initialize_system_data(world_path, systems, world)
    else:
        logger.info(f"generating a new world using theme: {world_prompt.theme}")
        world = generate_world(
            world_builder,
            world_path,
            world_prompt.theme,
            systems,
            room_count=room_count,
        )
        load_or_initialize_system_data(world_path, systems, world)

    # TODO: check if there have been any changes before saving
    save_world(world, world_file)
    save_system_data(world_path, systems)

    if add_rooms:
        new_rooms = []
        for i in range(add_rooms):
            logger.info(f"generating room {i + 1} of {add_rooms}")
            room = generate_room(
                world_builder, world, systems, current_room=i, total_rooms=add_rooms
            )
            new_rooms.append(room)
            world.rooms.append(room)

        # if the world was already full, no new rooms will be added
        if new_rooms:
            link_rooms(world_builder, world, systems, new_rooms)

    # create agents for each character after adding any new rooms
    create_agents(world, memory=memory, players=players)
    return (world, world_state_file, turn)


def simulate_world(world: World, systems: List[GameSystem], turns: int):
    # run game systems for each turn
    logger.info(f"simulating the world for {turns} turns using systems: {systems}")
    for i in count():
        current_turn = get_current_turn()
        logger.info(f"simulating turn {i} of {turns} (world turn {current_turn})")

        for system in systems:
            if system.simulate:
                logger.info(f"running system {system.name}")
                system.simulate(world, current_turn)

        set_current_turn(current_turn + 1)
        if i >= turns:
            logger.info("reached turn limit at world turn %s", current_turn + 1)
            break
