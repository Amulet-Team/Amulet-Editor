from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout

from amulet.level.abc import Level

from plugin.amulet.editor.dock.widget import DockWidget

from ._core import SelectionCoreWidget

SelectionWidgetIdentifier = "amulet.editor.SelectionWidget"


class SelectionWidget(DockWidget):
    def __init__(self, level: Level) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widget = SelectionCoreWidget()
        self._layout.addWidget(self._widget)

    @property
    def title(self) -> str:
        return "Selection"
