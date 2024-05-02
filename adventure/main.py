from json import load
from os import path

from packit.agent import Agent, agent_easy_connect
from packit.loops import loop_tool
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


def simulate_world(world: World, steps: int = 10, callback=None):
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
        ]
    )

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
            result = loop_tool(
                agent,
                (
                    "You are currently in {room_name}. {room_description}. "
                    "The room contains the following characters: {actors}. "
                    "The room contains the following items: {items}. "
                    "You can take the following actions: {actions}. "
                    "You can move in the following directions: {directions}. "
                    "What will you do next? Reply with a JSON function call, calling one of the actions."
                ),
                context={
                    "actions": [
                        "ask",
                        "give",
                        "look",
                        "move",
                        "take",
                        "tell",
                    ],  # , "use"],
                    "actors": room_actors,
                    "directions": room_directions,
                    "items": room_items,
                    "room_name": room.name,
                    "room_description": room.description,
                },
                result_parser=world_result_parser,
                toolbox=action_tools,
            )

            logger.info(f"{actor.name} step result: {result}")

            # if result was JSON, it has already been parsed and executed. anything remaining is flavor text
            # that should be presented back to the actor
            # TODO: inject this directly in the agent's memory rather than reprompting them
            response = agent(
                "The result of your last action was: {result}. Your turn is over, no further actions will be accepted. "
                'If you understand, reply with the word "end".',
                result=result,
            )

            logger.debug(f"{actor.name} step response: '{response}'")
            if response.strip().lower() not in ["end", ""]:
                logger.warning(
                    f"{actor.name} responded after the end of their turn: %s", response
                )
                response = agent(
                    "Your turn is over, no further actions will be accepted. Do not reply."
                )
                logger.debug(f"{actor.name} warning response: {response}")

        if callback:
            callback(world, current_step)

        current_step += 1


# main
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and simulate a fantasy world"
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
        default="world.json",
        help="The file to save the generated world to",
    )
    parser.add_argument(
        "--world-state",
        type=str,
        default="world-state.json",
        help="The file to save the world state to",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.world_state and path.exists(args.world_state):
        logger.info(f"Loading world state from {args.world_state}")
        with open(args.world_state, "r") as f:
            state = WorldState(**load(f))

        set_step(state.step)
        create_agents(state.world, state.memory)
        world = state.world
    elif args.world and path.exists(args.world):
        logger.info(f"Loading world from {args.world}")
        with open(args.world, "r") as f:
            world = World(**load(f))
            create_agents(world)
    else:
        logger.info(f"Generating a new {args.theme} world")
        llm = agent_easy_connect()
        agent = Agent(
            "world builder",
            f"You are an experienced game master creating a visually detailed {args.theme} world for a new adventure.",
            {},
            llm,
        )
        world = generate_world(agent, args.theme)
        create_agents(world)

    logger.debug("Loaded world: %s", world)

    if args.world:
        save_world(world, args.world)

    simulate_world(
        world,
        steps=args.steps,
        callback=lambda w, s: save_world_state(w, s, args.world_state),
    )


if __name__ == "__main__":
    main()
