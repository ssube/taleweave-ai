from pydantic import RootModel

from taleweave.utils.file import load_yaml, save_yaml


def load_system_data(cls, file):
    with open(file, "r") as f:
        data = load_yaml(f)

    return cls(**data)


def save_system_data(cls, file, model):
    data = RootModel[cls](model).model_dump()
    with open(file, "w") as f:
        save_yaml(f, data)
