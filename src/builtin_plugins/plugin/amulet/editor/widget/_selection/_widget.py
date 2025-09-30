from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout

from plugin.amulet.editor.widget.abc import TabWidget

from ._core import SelectionCoreWidget


SelectionWidgetIdentifier = "amulet.editor.SelectionWidget"


class SelectionWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widget = SelectionCoreWidget()
        self._layout.addWidget(self._widget)

    @property
    def title(self) -> str:
        return "Selection"
