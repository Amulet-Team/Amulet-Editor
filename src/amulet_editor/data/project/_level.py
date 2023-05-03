from typing import Optional

from amulet.api.level import BaseLevel
from amulet_editor.models.minecraft import LevelData

level_data: Optional[LevelData] = None

level: Optional[BaseLevel] = None


def get_level() -> Optional[BaseLevel]:
    return level
