import json as jsonlib
import pathlib
from typing import Any


class AmuletProject:
    def __init__(self, path: str):
        ext = pathlib.Path(path).suffix
        if ext == ".amulet-project":
            with open(path) as _amulet_project:
                self.__json: dict[str, dict] = jsonlib.load(_amulet_project)
            self.__path = path
        else:
            raise ValueError(
                f"Expected file extension '.amulet-project', found '{ext}'"
            )

    @property
    def packages(self) -> dict[str, list]:
        return self.__json.get("packages", {})

    @property
    def settings(self) -> dict[str, Any]:
        return self.__json.get("settings", {})

    def read(self) -> str:
        return jsonlib.dumps(self.__json, indent=4)

    def write(self, json: str):
        self.__json = jsonlib.loads(json)
        with open(self.__path) as _amulet_project:
            jsonlib.dump(self.__path, _amulet_project, indent=4)
