import os
from typing import Optional

from amulet_editor.data import system
from PySide6.QtCore import QStandardPaths


def application_data_directory() -> str:
    """Returns a path to the directory used for storage of persistent data.
    Generates appropriate directories if path does not already exist."""

    if system.is_windows():
        directory = os.path.join(
            os.getenv("APPDATA"),
            "Amulet-Editor",
        )
    elif system.is_mac():
        directory = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "Amulet-Editor",
        )
    elif system.is_linux():
        directory = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            "amulet-editor",
        )
    os.makedirs(directory, exist_ok=True)

    return directory


def project_directory(project_name: Optional[str] = None) -> str:
    """Returns a path to the default location for storing Amulet projects."""

    documents = str(os.path.sep).join(
        QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation).split("/")
    )

    directory = os.path.join(
        documents,
        "Amulet",
        "projects",
    )

    if project_name is not None:
        directory = os.path.join(directory, project_name)

    os.makedirs(directory, exist_ok=True)
    return directory
