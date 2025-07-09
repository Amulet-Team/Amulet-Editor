import os
import importlib.util

from ._application import data_directory

_first: str | None = None


def first_party_plugin_directory() -> str:
    global _first
    if _first is None:
        spec = importlib.util.find_spec("builtin_plugins")
        if spec is None:
            raise RuntimeError
        paths = spec.submodule_search_locations
        if not paths:
            raise RuntimeError
        _first = os.path.join(paths[0], "plugin")
    return _first


_third: str | None = None


def third_party_plugin_directory() -> str:
    """Returns the path within which dynamic plugins are stored."""
    global _third
    if _third is None:
        _third = os.path.abspath(os.path.join(data_directory(), "plugins"))
        os.makedirs(_third, exist_ok=True)
    return _third


def plugin_dirs() -> tuple[str, str]:
    return first_party_plugin_directory(), third_party_plugin_directory()
