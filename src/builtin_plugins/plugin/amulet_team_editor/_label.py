from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QHideEvent,
    QShowEvent,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QWidget


class QHoverLabel(QLabel):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(parent.window())

        self._parent = parent

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(7)
        self.shadow.setXOffset(1)
        self.shadow.setYOffset(1)
        self.shadow.setColor(QColor(0, 0, 0))

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setGraphicsEffect(self.shadow)
        self.setObjectName("hover_label")
        self.setText(text)

    def setText(self, text: str) -> None:
        super().setText(text)
        self.setFixedSize(self.minimumSizeHint() + QSize(30, 6))

    def showEvent(self, event: QShowEvent) -> None:
        window = self.parentWidget()
        parent = self._parent
        pos_gbl = parent.mapToGlobal(QPoint(0, 0))
        pos_rel = window.mapFromGlobal(pos_gbl)
        pos_mov = QPoint(
            pos_rel.x() + parent.width() + 3,
            pos_rel.y() + (parent.height() - self.height()) // 2,
        )
        self.move(pos_mov)

        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        parent = self.parent()
        assert isinstance(parent, QWidget)
        parent.update()  # Fix rendering artifacts
        return super().hideEvent(event)
