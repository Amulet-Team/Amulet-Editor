from PySide6.QtCore import QPoint
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QPushButton


class QHoverLabel(QPushButton):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(parent.window())
        self._parent = parent
        self.setText(text)

    def setText(self, text: str) -> None:
        super().setText(text)
        self.setFixedSize(self.sizeHint())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        window = self.parentWidget()
        if window is not None:
            parent = self._parent
            pos_rel = parent.mapTo(window, QPoint())
            self.move(
                pos_rel.x() + parent.width() + 3,
                pos_rel.y() + (parent.height() - self.height()) // 2,
            )
