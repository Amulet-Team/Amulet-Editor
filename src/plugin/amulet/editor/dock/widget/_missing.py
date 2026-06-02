from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from ._abc import DockWidget

MissingTabIdentifier = "amulet.editor.MissingWidget"


class MissingWidget(DockWidget):
    def __init__(self, identifier: str) -> None:
        super().__init__()

        self.identifier = identifier

        layout = QVBoxLayout(self)
        label = QLabel(identifier)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    @property
    def title(self) -> str:
        return self.identifier
