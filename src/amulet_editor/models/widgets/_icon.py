from typing import Optional

from amulet_editor.data.build import get_resource
from amulet_editor.models.widgets._label import QHoverLabel
from PySide6 import QtGui
from PySide6.QtCore import QEvent, QSize, QPoint
from PySide6.QtGui import QColor, QEnterEvent, QIcon, QPainter, QPaintEvent, QImage
from PySide6.QtWidgets import QToolButton, QWidget, QStyleOption, QStyle
from PySide6.QtSvgWidgets import QSvgWidget


class QSvgIcon(QIcon):
    def __init__(self, filename: str, size: QSize, color: QColor) -> None:
        pixmap = QIcon(filename).pixmap(size)

        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawRect(pixmap.rect())
        painter.end()

        super().__init__(pixmap)


class AStylableSvgWidget(QSvgWidget):
    """
    A subclass of QSvgWidget that adds support for colouring via style sheets.
    Set the background via QSS and this widget will merge the colour of the background with the transparency of the SVG icon.
    """
    def paintEvent(self, event: QPaintEvent):
        buffer = QImage(self.width(), self.height(), QImage.Format_ARGB32)
        buffer.fill(QColor(0, 0, 0, 0))  # Fill with transparency

        # Init the painter
        painter = QPainter(buffer)

        # Draw the SVG
        self.renderer().render(painter)

        # Use the alpha current alpha with the future colour
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        # Draw the normal background
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

        # Finish painting
        painter.end()

        # Draw the image to the widget.
        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), buffer)
        painter.end()
        print("paint")


class QIconButton(QToolButton):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._icon_name = "question-mark"
        self._icon_color = None

        self._hlbl_tooltip = QHoverLabel("", self)
        self._hlbl_tooltip.hide()

    def setIcon(self, icon_name: Optional[str] = None) -> None:
        if icon_name is not None:
            self._icon_name = icon_name

        icon_color = self._icon_color
        self._icon_color = (
            self.palette().brightText().color()
            if self.isChecked()
            else self.palette().text().color()
        )

        if icon_color != self._icon_color:
            super().setIcon(
                QSvgIcon(
                    get_resource(f"icons/tabler/{self._icon_name}"),
                    self.iconSize(),
                    self._icon_color,
                )
            )
            self.parent().update()  # Fix rendering artifacts

    def toolTip(self) -> QHoverLabel:
        return self._hlbl_tooltip

    def setToolTip(self, label: QHoverLabel) -> None:
        self._hlbl_tooltip = label

    def event(self, event: QEvent) -> bool:
        if type(event) == QtGui.QPaintEvent:
            self.setIcon()

        return super().event(event)

    def enterEvent(self, event: QEnterEvent):
        if len(self._hlbl_tooltip.text()) > 0:
            self._hlbl_tooltip.show()

    def leaveEvent(self, event: QEvent):
        self._hlbl_tooltip.hide()
