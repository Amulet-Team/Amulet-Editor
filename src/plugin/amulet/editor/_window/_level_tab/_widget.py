from .._tab import WindowTabClose

from PySide6.QtWidgets import QWidget

from amulet.level import Level


class LevelTabWidget(QWidget, WindowTabClose):
    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = level

    def close_tab(self) -> bool:
        print("close_tab", self._level.level_name)
        return True

    def hideEvent(self, event, /) -> None:
        print("hide", self._level.level_name)

    def showEvent(self, event, /) -> None:
        print("show", self._level.level_name)
