"""Utility class to create horizontal line separators."""

from typing import Optional
from PySide6.QtWidgets import QFrame, QWidget


class QHLine(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setProperty("borderTop", "surface")
