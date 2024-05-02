from typing import TYPE_CHECKING, Dict, List, Callable, Sequence
from random import choice, randint
from os import path
from json import dump, load, loads
from collections import deque

from pydantic import Field
from pydantic import RootModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage


from packit.agent import Agent, agent_easy_connect
from packit.results import multi_function_or_str_result
from packit.toolbox import Toolbox
from packit.utils import logger_with_colors
from packit.loops import loop_tool
from packit.utils import could_be_json

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass as dataclass  # noqa


logger = logger_with_colors(__name__)


# world building
Actions = Dict[str, Callable]


@dataclass
class Item:
    name: str
    description: str
    actions: Actions = Field(default_factory=dict)


@dataclass
class Actor:
    name: str
    backstory: str
    description: str
    health: int
    actions: Actions = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)


@dataclass
class Room:
    name: str
    description: str
    portals: Dict[str, str] = Field(default_factory=dict)
    items: List[Item] = Field(default_factory=list)
    actors: List[Actor] = Field(default_factory=list)
    actions: Actions = Field(default_factory=dict)


@dataclass
class World:
    rooms: List[Room]
    theme: str


@dataclass
class WorldState:
    world: World
    memory: Dict[str, List[str | Dict[str, str]]]
    step: int


# world generators
def generate_room(agent: Agent, world_theme: str, existing_rooms: List[str]) -> Room:
    name = agent(
        'Generate one room, area, or location that would make sense in the world of {world_theme}. Only respond with the room name, do not include the description or any other text. Do not prefix the name with "the", do not wrap it in quotes. The existing rooms are: {existing_rooms}',
        world_theme=world_theme,
        existing_rooms=existing_rooms,
    )
    logger.info(f"Generating room: {name}")
    desc = agent(
        "Generate a detailed description of the {name} area. What does it look like? What does it smell like? What can be seen or heard?",
        name=name,
    )

    items = []
    actors = []
    actions = {}

    return Room(
        name=name, description=desc, items=items, actors=actors, actions=actions
    )


def generate_item(
    agent: Agent,
    world_theme: str,
    dest_room: str | None = None,
    dest_actor: str | None = None,
    existing_items: List[str] = [],
) -> Item:
    if dest_actor:
        dest_note = "The item will be held by the {dest_actor} character"
    elif dest_room:
        dest_note = "The item will be placed in the {dest_room} room"
    else:
        dest_note = "The item will be placed in the world"

    name = agent(
        "Generate one item or object that would make sense in the world of {world_theme}. {dest_note}. "
        'Only respond with the item name, do not include a description or any other text. Do not prefix the name with "the", do not wrap it in quotes. '
        "Do not create any duplicate items in the same room. Do not give characters any duplicate items. The existing items are: {existing_items}",
        dest_note=dest_note,
        existing_items=existing_items,
        world_theme=world_theme,
    )
    logger.info(f"Generating item: {name}")
    desc = agent(
        "Generate a detailed description of the {name} item. What does it look like? What is it made of? What does it do?",
        name=name,
    )

    actions = {}

    return Item(name=name, description=desc, actions=actions)


def generate_actor(
    agent: Agent, world_theme: str, dest_room: str, existing_actors: List[str] = []
) -> Actor:
    name = agent(
        "Generate one person or creature that would make sense in the world of {world_theme}. The character will be placed in the {dest_room} room. "
        'Only respond with the character name, do not include a description or any other text. Do not prefix the name with "the", do not wrap it in quotes. '
        "Do not create any duplicate characters in the same room. The existing characters are: {existing_actors}",
        dest_room=dest_room,
        existing_actors=existing_actors,
        world_theme=world_theme,
    )
    logger.info(f"Generating actor: {name}")
    description = agent(
        "Generate a detailed description of the {name} character. What do they look like? What are they wearing? What are they doing? Describe their appearance from the perspective of an outside observer.",
        name=name,
    )
    backstory = agent(
        'Generate a backstory for the {name} actor. Where are they from? What are they doing here? What are their goals? Make sure to phrase the backstory in the second person, starting with "you are" and speaking directly to {name}.',
        name=name,
    )

    health = 100
    actions = {}

    return Actor(
        name=name,
        backstory=backstory,
        description=description,
        health=health,
        actions=actions,
    )


def generate_world(agent: Agent, theme: str) -> World:
    room_count = randint(3, 5)
    logger.info(f"Generating a {theme} with {room_count} rooms")

    existing_actors: List[str] = []
    existing_items: List[str] = []

    # generate the rooms
    rooms = []
    for i in range(room_count):
        existing_rooms = [room.name for room in rooms]
        room = generate_room(agent, theme, existing_rooms)
        rooms.append(room)

        item_count = randint(0, 3)
        for j in range(item_count):
            item = generate_item(
                agent, theme, dest_room=room.name, existing_items=existing_items
            )
            room.items.append(item)
            existing_items.append(item.name)

        actor_count = randint(0, 3)
        for j in range(actor_count):
            actor = generate_actor(
                agent, theme, dest_room=room.name, existing_actors=existing_actors
            )
            room.actors.append(actor)
            existing_actors.append(actor.name)

            # generate the actor's inventory
            item_count = randint(0, 3)
            for k in range(item_count):
                item = generate_item(
                    agent, theme, dest_room=room.name, existing_items=existing_items
                )
                actor.items.append(item)
                existing_items.append(item.name)

    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
    }

    # TODO: generate portals to link the rooms together
    for room in rooms:
        directions = ["north", "south", "east", "west"]
        for direction in directions:
            if direction in room.portals:
                logger.debug(f"Room {room.name} already has a {direction} portal")
                continue

            opposite_direction = opposite_directions[direction]

            if randint(0, 1):
                dest_room = choice([r for r in rooms if r.name != room.name])

                # make sure not to create duplicate links
                if room.name in dest_room.portals.values():
                    logger.debug(
                        f"Room {dest_room.name} already has a portal to {room.name}"
                    )
                    continue

                if opposite_direction in dest_room.portals:
                    logger.debug(
                        f"Room {dest_room.name} already has a {opposite_direction} portal"
                    )
                    continue

                # create bidirectional links
                room.portals[direction] = dest_room.name
                dest_room.portals[opposite_directions[direction]] = room.name

    return World(rooms=rooms, theme=theme)


# memory space
current_world = None
current_room = None
current_actor = None
current_step = 0
actor_agents = {}
action_tools = None


# simulation
def check_current():
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


def action_look(target: str) -> str:
    _, action_room, action_actor = check_current()
    logger.info(f"{action_actor.name} looks at {target}")

    if target == action_room.name:
        logger.info(f"{action_actor.name} saw the {action_room.name} room")
        return action_room.description

    for actor in action_room.actors:
        if actor.name == target:
            logger.info(
                f"{action_actor.name} saw the {actor.name} actor in the {action_room.name} room"
            )
            return actor.description

    for item in action_room.items:
        if item.name == target:
            logger.info(
                f"{action_actor.name} saw the {item.name} item in the {action_room.name} room"
            )
            return item.description

    for item in action_actor.items:
        if item.name == target:
            logger.info(
                f"{action_actor.name} saw the {item.name} item in their inventory"
            )
            return item.description

    return "You do not see that item or character in the room."


def action_move(direction: str) -> str:
    action_world, action_room, action_actor = check_current()

    destination_name = action_room.portals.get(direction)
    if not destination_name:
        return f"You cannot move {direction} from here."

    destination_room = next(
        (room for room in action_world.rooms if room.name == destination_name), None
    )
    if not destination_room:
        return f"The {destination_name} room does not exist."

    logger.info(f"{action_actor.name} moves {direction} to {destination_name}")
    action_room.actors.remove(action_actor)
    destination_room.actors.append(action_actor)

    return f"You move {direction} and arrive at {destination_name}."


def action_take(item_name: str) -> str:
    _, action_room, action_actor = check_current()

    item = next((item for item in action_room.items if item.name == item_name), None)
    if item:
        logger.info(f"{action_actor.name} takes the {item_name} item")
        action_room.items.remove(item)
        action_actor.items.append(item)
        return "You take the {item_name} item and put it in your inventory."
    else:
        return "The {item_name} item is not in the room."


def action_ask(character: str, question: str) -> str:
    # capture references to the current actor and room, because they will be overwritten
    action_actor = current_actor
    action_room = current_room

    if not action_actor or not action_room:
        raise ValueError(
            "The current actor and room must be set before calling action_ask"
        )

    # sanity checks
    if character == action_actor.name:
        return "You cannot ask yourself a question. Stop talking to yourself."

    question_actor, question_agent = actor_agents.get(character, (None, None))
    if not question_actor:
        return f"The {character} character is not in the room."

    if not question_agent:
        return f"The {character} character does not exist."

    logger.info(f"{action_actor.name} asks {character}: {question}")
    answer = question_agent(f"{action_actor.name} asks you: {question}. Reply with your response. Do not include the question or any other text, only your reply to {action_actor.name}.")

    if could_be_json(answer) and action_tell.__name__ in answer:
        answer = loads(answer).get("parameters", {}).get("message", "")

    if len(answer.strip()) > 0:
        logger.info(f"{character} responds to {action_actor.name}: {answer}")
        return f"{character} responds: {answer}"

    return f"{character} does not respond."


def action_tell(character: str, message: str) -> str:
    # capture references to the current actor and room, because they will be overwritten
    action_actor = current_actor
    action_room = current_room

    if not action_actor or not action_room:
        raise ValueError(
            "The current actor and room must be set before calling action_tell"
        )

    # sanity checks
    if character == action_actor.name:
        return "You cannot tell yourself a message. Stop talking to yourself."

    question_actor, question_agent = actor_agents.get(character, (None, None))
    if not question_actor:
        return f"The {character} character is not in the room."

    if not question_agent:
        return f"The {character} character does not exist."

    logger.info(f"{action_actor.name} tells {character}: {message}")
    answer = question_agent(f"{action_actor.name} tells you: {message}. Reply with your response. Do not include the message or any other text, only your reply to {action_actor.name}.")

    if could_be_json(answer) and action_tell.__name__ in answer:
        answer = loads(answer).get("parameters", {}).get("message", "")

    if len(answer.strip()) > 0:
        logger.info(f"{character} responds to {action_actor.name}: {answer}")
        return f"{character} responds: {answer}"

    return f"{character} does not respond."


def action_give(character: str, item_name: str) -> str:
    _, action_room, action_actor = check_current()

    destination_actor = next(
        (actor for actor in action_room.actors if actor.name == character), None
    )
    if not destination_actor:
        return f"The {character} character is not in the room."

    item = next((item for item in action_actor.items if item.name == item_name), None)
    if not item:
        return f"You do not have the {item_name} item in your inventory."

    logger.info(f"{action_actor.name} gives {character} the {item_name} item")
    action_actor.items.remove(item)
    destination_actor.items.append(item)

    return f"You give the {item_name} item to {character}."


def action_stop() -> str:
    _, _, action_actor = check_current()
    logger.info(f"{action_actor.name} end their turn")
    return "You stop your actions and end your turn."


def world_result_parser(value, agent, **kwargs):
    global current_world
    global current_room
    global current_actor

    if not current_world:
        raise ValueError(
            "The current world must be set before calling world_result_parser"
        )

    logger.debug(f"parsing action for {agent.name}: {value}")

    current_actor = next(
        (
            inner_actor
            for inner_actor, inner_agent in actor_agents.values()
            if inner_agent == agent
        ),
        None,
    )
    current_room = next(
        (room for room in current_world.rooms if current_actor in room.actors), None
    )

    return multi_function_or_str_result(value, agent=agent, **kwargs)


def create_agents(world: World, memory: Dict[str, List[str | Dict[str, str]]] = {}):
    # set up agents for each actor
    global actor_agents

    llm = agent_easy_connect()
    # for each actor in each room in the world
    for room in world.rooms:
        for actor in room.actors:
            agent = Agent(actor.name, actor.backstory, {}, llm)
            agent.memory = restore_memory(memory.get(actor.name, []))
            actor_agents[actor.name] = (actor, agent)


def simulate_world(world: World, steps: int = 10, callback=None):
    logger.info("Simulating the world")

    # collect actors, so they are only processed once
    all_actors = [actor for room in world.rooms for actor in room.actors]

    # prep the actions
    global action_tools

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
    global current_step
    global current_world
    current_world = world

    # simulate each actor
    for i in range(steps):
        logger.info(f"Simulating step {current_step}")
        for actor in all_actors:
            _, agent = actor_agents[actor.name]
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
                "The result of your last action was: {result}. Your turn is over, no further actions will be accepted. If you understand, reply with the word \"end\".",
                result=result,
            )

            logger.info(f"{actor.name} step response: '{response}'")
            if response.strip().lower() not in ["end", ""]:
                logger.warning(f"{actor.name} responded after the end of their turn: %s", response)
                response = agent(
                    "Your turn is over, no further actions will be accepted. Do not reply."
                )
                logger.info(f"{actor.name} warning response: {response}")

        if callback:
            callback(world, current_step)

        current_step += 1


def graph_world(world: World, step: int):
    import graphviz

    graph = graphviz.Digraph(f"{world.theme}-{step}", format="png")
    for room in world.rooms:
        room_label = "\n".join([room.name, *[actor.name for actor in room.actors]])
        graph.node(room.name, room_label)  # , room.description)
        for direction, destination in room.portals.items():
            graph.edge(room.name, destination, label=direction)

    graph.render(directory="worlds", view=True)


def snapshot_world(world: World, step: int):
    # save the world itself, along with the step number of the memory of each agent
    json_world = RootModel[World](world).model_dump()

    json_memory = {}

    for actor, agent in actor_agents.values():
        json_memory[actor.name] = list(agent.memory)

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

        # TODO: reload agent memory
        global current_step

        current_step = state.step
        world = state.world
        create_agents(world, state.memory)
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
        with open(args.world, "w") as f:
            json_world = RootModel[World](world).model_dump_json(indent=2)
            f.write(json_world)

    def save_world_state(world, step):
        graph_world(world, step)
        if args.world_state:
            json_state = snapshot_world(world, step)
            with open(args.world_state, "w") as f:

                def dumper(obj):
                    if isinstance(obj, BaseMessage):
                        return {
                            "content": obj.content,
                            "type": obj.type,
                        }

                    raise ValueError(f"Cannot serialize {obj}")

                dump(json_state, f, default=dumper, indent=2)

    simulate_world(world, steps=args.steps, callback=save_world_state)


if __name__ == "__main__":
    main()
