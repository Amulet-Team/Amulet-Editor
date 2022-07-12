import errno
import json
import os
from datetime import datetime, timezone
from json import JSONDecodeError
from typing import Any, Optional

import amulet
from amulet_editor.data import paths
from amulet_editor.data.project import _level
from amulet_editor.models.generic import Observer
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.project import MCProjectMeta

_root: Optional[str] = None
_projects_json = os.path.join(paths.user_directory(), "projects.json")

changed = Observer(str)


def list_projects() -> list[MCProjectMeta]:
    """List of metadata for all recent projects."""

    if os.path.exists(_projects_json):
        try:
            with open(_projects_json) as _file:
                projects: list[dict[str, Any]] = json.load(_file)
        except JSONDecodeError:
            projects = []
    else:
        projects = []

    metaprojects = []
    for project in projects:
        metaprojects.append(MCProjectMeta(**project))

    return metaprojects


def remember_project(path: str) -> None:
    """Adds path to list of projects. If already in list, update last accessed timestamp."""

    if os.path.exists(_projects_json):
        try:
            with open(_projects_json) as _file:
                projects: list[dict[str, Any]] = json.load(_file)
        except JSONDecodeError:
            projects = []
    else:
        projects = []

    for project in projects:
        if project["path"] == path:
            project.update(
                {"last_opened": datetime.now().replace(tzinfo=timezone.utc).timestamp()}
            )
            break
    else:
        projects.append(
            {
                "path": f"{path}",
                "last_opened": datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            }
        )

    with open(_projects_json, "w") as _file:
        json.dump(projects, _file, indent=2)


def root() -> str:
    """Returns a path to the current project root directory if one exists."""
    return _root


def set_root(root: str) -> None:
    """Change project rood directory."""
    global _root

    remember_project(root)

    _root = root
    changed.emit(root)


def open_world(root: str) -> None:
    """Open a minecraft world folder as a project."""

    dat_file = os.path.join(root, "level.dat")
    if not os.path.isfile(dat_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dat_file)
    else:
        _level.level_data = LevelData(amulet.load_format(root))

    amulet_dir = os.path.join(root, ".amulet")
    if not os.path.isdir(amulet_dir):
        os.makedirs(amulet_dir, exist_ok=True)

    set_root(root)


def open_project(root: str) -> None:
    """Open existing project at root folder."""

    amulet_dir = os.path.join(root, ".amulet")
    if not os.path.isdir(amulet_dir):
        os.makedirs(amulet_dir, exist_ok=True)

    set_root(root)
