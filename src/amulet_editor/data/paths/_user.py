import os

from amulet_editor.data.paths._application import application_directory


def user_directory() -> str:
    directory = os.path.join(application_directory(), "user")
    os.makedirs(directory, exist_ok=True)

    return directory
