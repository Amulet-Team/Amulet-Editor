import json as jsonlib
import os
import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(order=True)
class MCProjectMeta:
    sort_index: int = field(init=False, repr=False)

    path: str
    last_opened: datetime
    exists: bool = field(init=False)

    def __post_init__(self):
        if isinstance(self.last_opened, float):
            self.last_opened = datetime.fromtimestamp(self.last_opened)
        self.exists = os.path.isdir(self.path)
        self.sort_index = self.last_opened


class MCProject:
    def __init__(self, path: str) -> None:
        ext = pathlib.Path(path).suffix
        if ext == ".mcproject":
            with open(path) as _amulet_project:
                self.__json: dict[str, dict] = jsonlib.load(_amulet_project)
            self.__path = path
        else:
            raise ValueError(f"Expected file extension '.mcproject', found '{ext}'")

    @property
    def packages(self) -> dict[str, list]:
        return self.__json.get("packages", {})

    @property
    def settings(self) -> dict[str, Any]:
        return self.__json.get("settings", {})

    def read(self) -> str:
        return jsonlib.dumps(self.__json, indent=4)

    def write(self, json: str) -> None:
        self.__json = jsonlib.loads(json)
        with open(self.__path) as _amulet_project:
            jsonlib.dump(self.__path, _amulet_project, indent=4)
