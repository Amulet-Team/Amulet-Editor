from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from plugin.amulet.editor.window import TabWidget

from ._core import SelectionCoreWidget


class SelectionWidget(TabWidget):
    name = "Selection"

    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._widget = SelectionCoreWidget()
        self._layout.addWidget(self._widget)
