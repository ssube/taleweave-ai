from argparse import ArgumentParser
from json import dumps

from pydantic import TypeAdapter

from taleweave.models.entity import Character, Item, Portal, Room, World
from taleweave.utils.file import load_yaml
from taleweave.utils.world import describe_entity

MODELS = {
    "character": Character,
    "item": Item,
    "portal": Portal,
    "room": Room,
    "world": World,
}


def parse_args():
    parser = ArgumentParser(
        description="Generate or validate a schema for the TaleWeave AI models"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.required = True

    generate_parser = subparsers.add_parser(
        "generate", help="Generate a schema for a model"
    )
    generate_parser.add_argument(
        "model",
        type=str,
        choices=list(MODELS.keys()),
        help="The name of the model to generate a schema for",
    )

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a JSON file against a model schema"
    )
    validate_parser.add_argument(
        "model",
        type=str,
        choices=list(MODELS.keys()),
        help="The name of the model to validate against",
    )
    validate_parser.add_argument(
        "file",
        type=str,
        help="The path to the JSON file to validate",
    )

    return parser.parse_args()


def command_generate(args):
    model = MODELS[args.model]
    schema = TypeAdapter(model).json_schema()
    print(dumps(schema, indent=2))


def command_validate(args):
    model = MODELS[args.model]
    with open(args.file, "r") as file:
        data = load_yaml(file)

    entity = model(**data)
    if isinstance(entity, World):
        print(entity)
    else:
        print(describe_entity(entity))


COMMANDS = {
    "generate": command_generate,
    "validate": command_validate,
}


def main():
    args = parse_args()
    command = COMMANDS[args.command]
    command(args)


if __name__ == "__main__":
    main()
