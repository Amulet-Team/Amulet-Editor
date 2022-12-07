import os
from ._application import application_directory


def plugin_directory():
    """Returns the path within which dynamic plugins are stored."""
    path = os.path.join(application_directory(), "plugins")
    os.makedirs(path, exist_ok=True)
    return path
