from importlib import import_module
from json import load
from os import environ, path

from dotenv import load_dotenv
from packit.agent import Agent, agent_easy_connect
from packit.loops import loop_retry
from packit.results import multi_function_or_str_result
from packit.toolbox import Toolbox
from packit.utils import logger_with_colors

from adventure.actions import (
    action_ask,
    action_give,
    action_look,
    action_move,
    action_take,
    action_tell,
)
from adventure.context import (
    get_actor_for_agent,
    get_agent_for_actor,
    get_current_world,
    get_step,
    set_current_actor,
    set_current_room,
    set_current_world,
    set_step,
)
from adventure.generate import generate_world
from adventure.models import World, WorldState
from adventure.state import create_agents, save_world, save_world_state

logger = logger_with_colors(__name__)

load_dotenv(environ.get("ADVENTURE_ENV", ".env"), override=True)


# simulation
def world_result_parser(value, agent, **kwargs):
    current_world = get_current_world()
    if not current_world:
        raise ValueError(
            "The current world must be set before calling world_result_parser"
        )

    logger.debug(f"parsing action for {agent.name}: {value}")

    current_actor = get_actor_for_agent(agent)
    current_room = next(
        (room for room in current_world.rooms if current_actor in room.actors), None
    )

    set_current_room(current_room)
    set_current_actor(current_actor)

    return multi_function_or_str_result(value, agent=agent, **kwargs)


def simulate_world(world: World, steps: int = 10, callback=None, extra_actions=[]):
    logger.info("Simulating the world")

    # collect actors, so they are only processed once
    all_actors = [actor for room in world.rooms for actor in room.actors]

    # TODO: add actions for: drop, use, attack, cast, jump, climb, swim, fly, etc.
    action_tools = Toolbox(
        [
            action_ask,
            action_give,
            action_look,
            action_move,
            action_take,
            action_tell,
            *extra_actions,
        ]
    )
    action_names = action_tools.list_tools()

    # create a result parser that will memorize the actor and room
    set_current_world(world)

    # simulate each actor
    for i in range(steps):
        current_step = get_step()
        logger.info(f"Simulating step {current_step}")
        for actor in all_actors:
            agent = get_agent_for_actor(actor)
            if not agent:
                logger.error(f"Agent not found for actor {actor.name}")
                continue

            room = next((room for room in world.rooms if actor in room.actors), None)
            if not room:
                logger.error(f"Actor {actor.name} is not in a room")
                continue

            room_actors = [actor.name for actor in room.actors]
            room_items = [item.name for item in room.items]
            room_directions = list(room.portals.keys())

            logger.info("starting actor %s turn", actor.name)
            result = loop_retry(
                agent,
                (
                    "You are currently in {room_name}. {room_description}. "
                    "The room contains the following characters: {actors}. "
                    "The room contains the following items: {items}. "
                    "You can take the following actions: {actions}. "
                    "You can move in the following directions: {directions}. "
                    "What will you do next? Reply with a JSON function call, calling one of the actions."
                    "You can only take one action per turn. Pick the most important action and save the rest for later."
                    "What is your action?"
                ),
                context={
                    "actions": action_names,
                    "actors": room_actors,
                    "directions": room_directions,
                    "items": room_items,
                    "room_name": room.name,
                    "room_description": room.description,
                },
                result_parser=world_result_parser,
                toolbox=action_tools,
            )

            logger.debug(f"{actor.name} step result: {result}")
            agent.memory.append(result)

        if callback:
            callback(world, current_step)

        set_step(current_step + 1)


# main
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and simulate a fantasy world"
    )
    parser.add_argument(
        "--actions", type=str, help="Extra actions to include in the simulation"
    )
    parser.add_argument(
        "--flavor", type=str, help="Some additional flavor text for the generated world"
    )
    parser.add_argument(
        "--player", type=str, help="The name of the character to play as"
    )
    parser.add_argument(
        "--rooms", type=int, default=5, help="The number of rooms to generate"
    )
    parser.add_argument(
        "--max-rooms", type=int, help="The maximum number of rooms to generate"
    )
    parser.add_argument(
        "--state",
        type=str,
        # default="world.state.json",
        help="The file to save the world state to. Defaults to $world.state.json, if not set",
    )
    parser.add_argument(
        "--steps", type=int, default=10, help="The number of simulation steps to run"
    )
    parser.add_argument(
        "--theme", type=str, default="fantasy", help="The theme of the generated world"
    )
    parser.add_argument(
        "--world",
        type=str,
        default="world",
        help="The file to save the generated world to",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    world_file = args.world + ".json"
    world_state_file = args.state or (args.world + ".state.json")

    players = []
    if args.player:
        players.append(args.player)

    memory = {}
    if path.exists(world_state_file):
        logger.info(f"Loading world state from {world_state_file}")
        with open(world_state_file, "r") as f:
            state = WorldState(**load(f))

        set_step(state.step)

        memory = state.memory
        world = state.world
        world.name = args.world
    elif path.exists(world_file):
        logger.info(f"Loading world from {world_file}")
        with open(world_file, "r") as f:
            world = World(**load(f))
    else:
        logger.info(f"Generating a new {args.theme} world")
        llm = agent_easy_connect()
        agent = Agent(
            "World Builder",
            f"You are an experienced game master creating a visually detailed {args.theme} world for a new adventure. {args.flavor}",
            {},
            llm,
        )
        world = generate_world(
            agent, args.world, args.theme, rooms=args.rooms, max_rooms=args.max_rooms
        )
        save_world(world, world_file)

    create_agents(world, memory=memory, players=players)

    # load extra actions
    extra_actions = []
    if args.actions:
        logger.info(f"Loading extra actions from {args.actions}")
        action_module, action_function = args.actions.rsplit(":", 1)
        action_module = import_module(action_module)
        action_function = getattr(action_module, action_function)
        module_actions = action_function()
        logger.info(
            f"Loaded extra actions: {[action.__name__ for action in module_actions]}"
        )
        extra_actions.extend(module_actions)

    logger.debug("Simulating world: %s", world)
    simulate_world(
        world,
        steps=args.steps,
        callback=lambda w, s: save_world_state(w, s, world_state_file),
        extra_actions=extra_actions,
    )


if __name__ == "__main__":
    main()
