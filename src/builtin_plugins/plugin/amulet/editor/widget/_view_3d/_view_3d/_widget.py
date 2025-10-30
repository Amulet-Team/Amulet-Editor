from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from plugin.amulet.editor.widget.abc import TabWidget

from ._canvas import FirstPersonCanvas


ViewportWidgetIdentifier = "amulet.editor.ViewportWidget"


class ViewportWidget(TabWidget):
    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(FirstPersonCanvas())

    @property
    def title(self) -> str:
        return "Viewport"
