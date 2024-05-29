from json import dumps
from logging import getLogger
from queue import Queue
from readline import add_history
from typing import Any, Callable, Dict, List, Optional, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from packit.agent import Agent

from taleweave.context import action_context
from taleweave.models.event import PromptEvent

logger = getLogger(__name__)


# Dict[client, player]
active_players: Dict[str, "BasePlayer"] = {}


def get_player(client: str) -> Optional["BasePlayer"]:
    """
    Get a player by name.
    """

    return active_players.get(client, None)


def set_player(client: str, player: "BasePlayer"):
    """
    Add a player to the active players.
    """

    if has_player(player.name):
        raise ValueError(f"Someone is already playing as {player.name}!")

    active_players[client] = player


def remove_player(client: str):
    """
    Remove a player from the active players.
    """

    if client in active_players:
        del active_players[client]


def has_player(character_name: str) -> bool:
    """
    Check if a character is already being played.
    """

    return character_name in [player.name for player in active_players.values()]


def list_players():
    return {client: player.name for client, player in active_players.items()}


class BasePlayer:
    """
    A human agent that can interact with the world.
    """

    name: str
    backstory: str
    memory: List[str | BaseMessage]

    def __init__(self, name: str, backstory: str) -> None:
        self.name = name
        self.backstory = backstory
        self.memory = []

    def load_history(self, lines: Sequence[str | BaseMessage]):
        """
        Load the history of the player's input.
        """

        self.memory.extend(lines)

        for line in lines:
            if isinstance(line, BaseMessage):
                add_history(str(line.content))
            else:
                add_history(line)

    def invoke(self, prompt: str, context: Dict[str, Any], **kwargs) -> Any:
        """
        Ask the player for input.
        """

        return self(prompt, **context)

    def parse_pseudo_function(self, reply: str):
        # turn other replies into a JSON function call
        action, *param_rest = reply.split(":", 1)
        param_str = ",".join(param_rest or [])
        param_pairs = param_str.split(",")

        def parse_value(value: str) -> str | bool | float | int:
            if value.startswith("~"):
                return value[1:]
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"
            if value.isdecimal():
                return float(value)
            if value.isnumeric():
                return int(value)
            return value

        params = {
            key.strip(): parse_value(value.strip())
            for key, value in (
                pair.split("=", 1) for pair in param_pairs if len(pair.strip()) > 0
            )
        }

        reply_json = dumps(
            {
                "function": action,
                "parameters": params,
            }
        )
        return reply_json

    def parse_input(self, reply: str):
        # if the reply starts with a tilde, it is a function response and should be parsed without the tilde
        if reply.startswith("~"):
            reply = self.parse_pseudo_function(reply[1:])

        self.memory.append(AIMessage(content=reply))
        return reply

    def __call__(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class LocalPlayer(BasePlayer):
    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Ask the player for input.
        """

        logger.info("prompting local player: {self.name}")

        formatted_prompt = prompt.format(**kwargs)
        self.memory.append(HumanMessage(content=formatted_prompt))
        print(formatted_prompt)

        reply = input(">>> ")
        reply = reply.strip()

        return self.parse_input(reply)


class RemotePlayer(BasePlayer):
    fallback_agent: Agent | None
    input_queue: Queue[str]
    send_prompt: Callable[[PromptEvent], bool]

    def __init__(
        self,
        name: str,
        backstory: str,
        send_prompt: Callable[[PromptEvent], bool],
        fallback_agent=None,
    ) -> None:
        super().__init__(name, backstory)
        self.fallback_agent = fallback_agent
        self.input_queue = Queue()
        self.send_prompt = send_prompt

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Ask the player for input.
        """

        formatted_prompt = prompt.format(**kwargs)
        self.memory.append(HumanMessage(content=formatted_prompt))

        with action_context() as (current_room, current_character):
            prompt_event = PromptEvent(
                prompt=formatted_prompt, room=current_room, character=current_character
            )

            try:
                logger.info(f"prompting remote player: {self.name}")
                if self.send_prompt(prompt_event):
                    reply = self.input_queue.get(timeout=60)
                    logger.info(f"got reply from remote player: {reply}")
                    return self.parse_input(reply)
            except Exception:
                logger.exception("error getting reply from remote player")

            if self.fallback_agent:
                logger.info("prompting fallback agent: {self.fallback_agent.name}")
                return self.fallback_agent(prompt, **kwargs)

            return ""
