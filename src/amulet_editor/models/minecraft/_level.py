from datetime import datetime, timezone
from typing import Optional, Union

import amulet
from amulet.level.formats.anvil_world.format import AnvilFormat
from amulet.level.formats.leveldb_world.format import LevelDBFormat
from amulet_editor.models.text import Motd


class LevelData:
    def __init__(self, level_format: Union[AnvilFormat, LevelDBFormat]):
        self.load_format(level_format)

    def load_format(self, level_format: Union[AnvilFormat, LevelDBFormat]):
        if isinstance(level_format, AnvilFormat):
            last_played = datetime.utcfromtimestamp(level_format.last_played / 1000)
        elif isinstance(level_format, LevelDBFormat):
            last_played = datetime.utcfromtimestamp(level_format.last_played)
        else:
            raise TypeError(
                "expected AnvilFormat or LevelDBFormat object, {} found".format(
                    type(level_format)
                )
            )

        self._edition = level_format.platform.title()
        self._icon_path = (
            level_format.world_image_path
            if amulet.IMG_DIRECTORY not in level_format.world_image_path
            else None
        )
        self._name = Motd(level_format.level_name)
        self._path = level_format.path
        self._last_played = last_played.replace(tzinfo=timezone.utc)
        self._version = level_format.game_version_string.split(" ")[1]

    @property
    def edition(self) -> str:
        return self._edition

    @property
    def icon_path(self) -> Optional[str]:
        return self._icon_path

    @property
    def last_played(self) -> datetime:
        return self._last_played

    @property
    def name(self) -> Motd:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def version(self) -> str:
        return self._version
