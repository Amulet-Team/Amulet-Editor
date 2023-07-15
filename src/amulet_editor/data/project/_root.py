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

_root: Optional[str] = None

changed = Observer(str)


def _projects_json():
    return os.path.join(paths.user_directory(), "projects.json")


def remember_project(path: str):
    """Adds path to list of projects. If already in list, update last accessed timestamp."""

    if os.path.exists(_projects_json()):
        try:
            with open(_projects_json()) as _file:
                _projects: list[dict[str, Any]] = json.load(_file)
        except JSONDecodeError:
            _projects = []
    else:
        _projects = []

    for _project in _projects:
        if _project["path"] == path:
            _project.update(
                {"last_opened": datetime.now().replace(tzinfo=timezone.utc).timestamp()}
            )
            break
    else:
        _projects.append(
            {
                "path": f"{path}",
                "last_opened": datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            }
        )

    with open(_projects_json(), "w") as _file:
        json.dump(_projects, _file, indent=2)


def root() -> str:
    """Returns a path to the current project root directory if one exists."""
    return _root


def set_root(path: str):
    """Changes the root directory of the current project."""
    global _root

    if os.path.exists(os.path.join(path, "level.dat")):
        _level.level_data = LevelData(amulet.load_format(path))

    remember_project(path)

    _root = path
    changed.emit(path)
