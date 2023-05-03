import os
from typing import Optional

from PySide6.QtCore import QStandardPaths


def application_data_directory() -> str:
    """Returns a path to the directory used for storage of persistent data.
    Generates appropriate directories if path does not already exist."""

    directory = os.path.join(
        os.path.normpath(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
        ),
        "Amulet-Editor",
    )
    os.makedirs(directory, exist_ok=True)
    return directory


def logging_directory() -> str:
    directory = os.path.join(application_data_directory(), "logs")
    os.makedirs(directory, exist_ok=True)
    return directory


def project_directory(project_name: Optional[str] = None) -> str:
    """Returns a path to the default location for storing Amulet projects."""

    documents = os.path.normpath(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
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
