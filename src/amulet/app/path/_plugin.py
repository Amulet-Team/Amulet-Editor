import os
import importlib.util

from ._application import data_directory


_builtin_plugin_dir: str | None = None


def first_party_plugin_directory() -> str:
    global _builtin_plugin_dir
    if _builtin_plugin_dir is None:
        spec = importlib.util.find_spec("builtin_plugins")
        if spec is None:
            raise RuntimeError
        paths = spec.submodule_search_locations
        if not paths:
            raise RuntimeError
        _builtin_plugin_dir = paths[0]
    return _builtin_plugin_dir


def third_party_plugin_directory() -> str:
    """Returns the path within which dynamic plugins are stored."""
    path = os.path.abspath(os.path.join(data_directory(), "plugins"))
    os.makedirs(path, exist_ok=True)
    return path
