from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout

from amulet.level.abc import Level

from plugin.amulet.editor.dock.widget import DockWidget

from ._canvas import FirstPersonCanvas

ViewportWidgetIdentifier = "amulet.editor.ViewportWidget"


class ViewportWidget(DockWidget):
    def __init__(self, level: Level):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(FirstPersonCanvas())

    @property
    def title(self) -> str:
        return "Viewport"
