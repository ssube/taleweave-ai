from importlib import import_module


def load_plugin(name: str, override_function: str | None = None):
    plugin_entry = get_plugin_function(name, override_function)
    return plugin_entry()


def get_plugin_function(name: str, override_function: str | None = None):
    module_name, *rest = name.rsplit(":", 1)
    function_name = rest[0] if rest else "init"
    plugin_module = import_module(module_name)
    return getattr(plugin_module, override_function or function_name)
