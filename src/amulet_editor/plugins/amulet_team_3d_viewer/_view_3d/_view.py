from __future__ import annotations

from typing import Optional
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from amulet_team_main_window.application.windows.main_window import View

from ._renderer import FirstPersonCanvas


class View3D(QWidget, View):
    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(FirstPersonCanvas())
