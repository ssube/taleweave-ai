from json import dumps
from readline import add_history
from typing import Any, Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from packit.utils import could_be_json


class LocalPlayer:
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

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Ask the player for input.
        """

        formatted_prompt = prompt.format(**kwargs)
        self.memory.append(HumanMessage(content=formatted_prompt))
        print(formatted_prompt)

        reply = input(">>> ")
        reply = reply.strip()

        # if the reply starts with a tilde, it is a literal response and should be returned without the tilde
        if reply.startswith("~"):
            reply = reply[1:]
            self.memory.append(AIMessage(content=reply))
            return reply

        # if the reply is JSON or a special command, return it as-is
        if could_be_json(reply) or reply.lower() in ["end", ""]:
            self.memory.append(AIMessage(content=reply))
            return reply

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
        self.memory.append(AIMessage(content=reply_json))
        return reply_json