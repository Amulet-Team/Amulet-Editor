from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtGui import QShowEvent

from amulet.level.abc import Level


class MetadataWidgetP(QWidget):
    def __init__(self, level: Level):
        super().__init__()
        self._level = level


class MetadataTool(QWidget):
    def __init__(self, level: Level):
        super().__init__()
        self._level = level
        self._widget: MetadataWidgetP | None = None

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._widget is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self._widget = MetadataWidgetP(self._level)
            layout.addWidget(self._widget)
