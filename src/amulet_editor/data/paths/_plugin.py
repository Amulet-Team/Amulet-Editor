import os

import amulet_editor
from ._application import data_directory


def first_party_plugin_directory() -> str:
    return os.path.abspath(os.path.join(amulet_editor.__path__[0], "plugins"))


def third_party_plugin_directory() -> str:
    """Returns the path within which dynamic plugins are stored."""
    path = os.path.abspath(os.path.join(data_directory(), "plugins"))
    os.makedirs(path, exist_ok=True)
    return path
