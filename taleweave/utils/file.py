from yaml import Loader, dump, load


def load_yaml(file):
    return load(file, Loader=Loader)


def save_yaml(file, data):
    return dump(data, file)
