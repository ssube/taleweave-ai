from yaml import Loader, dump, load

# this module MUST NOT import any other taleweave modules, since it is used to initialize the logger


def load_yaml(file):
    return load(file, Loader=Loader)


def save_yaml(file, data):
    return dump(data, file)
