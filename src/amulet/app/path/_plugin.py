import os
import importlib.util

from ._application import data_directory

_first: str | None = None


def first_party_plugin_directory() -> str:
    global _first
    if _first is None:
        spec = importlib.util.find_spec("plugin")
        if spec is None:
            raise RuntimeError
        paths = spec.submodule_search_locations
        if not paths:
            raise RuntimeError
        _first = paths[0]
    return _first


_third: str | None = None


def third_party_plugin_directory() -> str:
    """Returns the path within which dynamic plugins are stored."""
    global _third
    if _third is None:
        _third = os.path.abspath(os.path.join(data_directory(), "plugins"))
        os.makedirs(_third, exist_ok=True)
    return _third
