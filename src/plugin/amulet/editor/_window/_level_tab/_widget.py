from .._tab import WindowTabClose

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget

from amulet.level import Level

from ._toolbar import ToolBar


class LevelTabWidget(QWidget, WindowTabClose):
    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = level

        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._toolbar = ToolBar(Qt.Orientation.Vertical)
        self._main_layout.addWidget(self._toolbar)

        self._layouts = QStackedWidget()
        self._main_layout.addWidget(self._layouts, 1)

        self._initialised = False

    def close_tab(self) -> bool:
        # TODO: If the level has unsaved changes, ask the user if they want to save them.
        return True

    def showEvent(self, event: QShowEvent, /) -> None:
        if not self._initialised:
            from .._main_window import get_amulet_editor
            self._initialised = True
            get_amulet_editor().level_tab_init.emit(self._level)


class LevelTabWidgetAPI:
    def __init__(self, level_tab: LevelTabWidget) -> None:
        self._level_tab = level_tab

