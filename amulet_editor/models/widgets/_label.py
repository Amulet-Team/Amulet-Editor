import math

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QHideEvent,
    QResizeEvent,
    QShowEvent,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QSizePolicy, QWidget


class QElidedLabel(QLabel):
    def __init__(self, text: str = "", parent: QWidget = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self._text = text
        self._text_elide_mode = Qt.ElideRight
        self._text_width = 0
        self._width_hint = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._format_text()

    def sizeHint(self) -> QSize:
        width = self.width()
        doc = QTextDocument()
        try:
            doc.setDefaultFont(self.font())
            doc.setHtml(self._text)
            width = math.ceil(doc.idealWidth()) + 1
        finally:
            doc.deleteLater()

        return QSize(width, super().sizeHint().height())

    def elideMode(self) -> Qt.TextElideMode:
        return self._text_elide_mode

    def setElideMode(self, mode: Qt.TextElideMode) -> None:
        self._text_elide_mode = (
            Qt.ElideNone
            if mode not in [Qt.ElideNone, Qt.ElideLeft, Qt.ElideRight, Qt.ElideMiddle]
            else mode
        )
        self._format_text()

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        self._text = text
        self._format_text()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._format_text()

    def _format_text(self) -> None:
        super().setText(self._elide_text(self._text))

    def _elide_text(self, text: str):
        doc = QTextDocument()
        max_width = self.width()
        metric = QFontMetrics(self.font())

        try:
            doc.setDefaultFont(self.font())
            doc.setHtml(text)

            # Return text without changes if it fits within label
            ideal_width = doc.idealWidth()
            if ideal_width <= max_width:
                self._text_width = ideal_width
                return text

            # Determine ellipses and cursor position
            cursor = QTextCursor(doc)
            if self._text_elide_mode == Qt.ElideNone:
                ellipses = ""
                character_count = doc.characterCount()
                cursor.setPosition(character_count - 1)
                delete_previous = True
            elif self._text_elide_mode == Qt.ElideLeft:
                ellipses = "\u2026"
                cursor.setPosition(0)
                delete_previous = False
            elif self._text_elide_mode == Qt.ElideRight:
                ellipses = "\u2026"
                character_count = doc.characterCount()
                cursor.setPosition(character_count - 1)
                delete_previous = True
            elif self._text_elide_mode == Qt.ElideMiddle:
                ellipses = "\u2026"
                character_count = doc.characterCount()
                cursor.setPosition(math.ceil(character_count / 2))
                delete_previous = True

            # Remove characters until ellipses fits
            max_width = max_width - metric.horizontalAdvance(ellipses)
            while doc.idealWidth() > max_width:
                if delete_previous:
                    cursor.deletePreviousChar()
                else:
                    cursor.deleteChar()

                if self._text_elide_mode == Qt.ElideMiddle:
                    delete_previous = not delete_previous

            # Add ellipses after removing characters so they match trailing html formatting
            if self._text_elide_mode == Qt.ElideLeft:
                cursor.setPosition(0)
            elif self._text_elide_mode == Qt.ElideRight:
                character_count = doc.characterCount()
                cursor.setPosition(character_count - 1)
            cursor.insertText(ellipses)

            self._text_width = ideal_width
            return doc.toHtml()
        finally:
            doc.deleteLater()


class QHoverLabel(QLabel):
    def __init__(self, text: str, ref: QWidget):
        super().__init__(ref)

        self._ref_widget = ref

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(7)
        self.shadow.setXOffset(1)
        self.shadow.setYOffset(1)
        self.shadow.setColor(QColor(0, 0, 0))

        self.setAlignment(Qt.AlignCenter)
        self.setGraphicsEffect(self.shadow)
        self.setObjectName("hover_label")
        self.setParent(self.window())
        self.setText(text)

    def setText(self, text: str) -> None:
        super().setText(text)
        self.setFixedSize(self.minimumSizeHint() + QSize(30, 6))

    def showEvent(self, event: QShowEvent) -> None:
        pos_gbl = self._ref_widget.parent().mapToGlobal(self._ref_widget.pos())
        pos_rel = self.parent().mapFromGlobal(pos_gbl)
        pos_mov = QPoint(
            pos_rel.x() + self._ref_widget.width() + 3,
            pos_rel.y() + (self._ref_widget.height() - self.height()) // 2,
        )
        self.move(pos_mov)

        self.parent().update()  # Fix rendering artifacts
        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self.parent().update()  # Fix rendering artifacts
        return super().hideEvent(event)
