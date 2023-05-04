from typing import Optional

from amulet_editor.data import build
from amulet_editor.models.widgets._label import QHoverLabel
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QColor, QEnterEvent, QPainter, QPaintEvent, QImage
from PySide6.QtWidgets import QWidget, QStyleOption, QStyle, QVBoxLayout, QPushButton
from PySide6.QtSvgWidgets import QSvgWidget


class AStylableSvgWidget(QSvgWidget):
    """
    A subclass of QSvgWidget that adds support for colouring via style sheets.
    Set the background via QSS and this widget will merge the colour of the background with the transparency of the SVG icon.
    """

    def paintEvent(self, event: QPaintEvent):
        buffer_width = max(self.width(), 50)
        buffer_height = max(self.height(), 50)

        buffer = QImage(buffer_width, buffer_height, QImage.Format.Format_ARGB32)
        buffer.fill(QColor(0, 0, 0, 0))  # Fill with transparency

        # Init the painter
        painter = QPainter(buffer)

        # Draw the SVG
        self.renderer().render(painter)
        # If the buffer is larger than the widget apply scaling
        painter.scale(buffer_width / self.width(), buffer_height / self.height())

        # Use the alpha current alpha with the future colour
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        # Draw the normal background
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget, opt, painter, self
        )

        # Finish painting
        painter.end()

        # Draw the image to the widget.
        painter = QPainter(self)
        painter.drawImage(self.rect(), buffer)
        painter.end()


class AIconButton(QPushButton):
    """A QPushButton containing a stylable icon."""

    def __init__(self, icon_name: str = "question-mark.svg", parent: QWidget = None):
        super().__init__(parent)
        self.setProperty("hover", "false")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon = AStylableSvgWidget(build.get_resource(f"icons/tabler/{icon_name}"))
        self._layout.addWidget(self._icon)

    def setIcon(self, icon_name: Optional[str] = None):
        self._icon.load(build.get_resource(f"icons/tabler/{icon_name}"))

    def setIconSize(self, size: QSize):
        self._icon.setFixedSize(size)

    def enterEvent(self, event: QEnterEvent):
        self.setProperty("hover", "true")
        self.setStyleSheet("/* /")  # Force a style update.
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        if not self.isChecked():
            self.setProperty("hover", "false")
        self.setStyleSheet("/* /")  # Force a style update.
        super().leaveEvent(event)


class ATooltipIconButton(AIconButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hlbl_tooltip: Optional[QHoverLabel] = None

    def enterEvent(self, event: QEnterEvent):
        if self._hlbl_tooltip is not None and len(self._hlbl_tooltip.text()) > 0:
            self._hlbl_tooltip.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        if self._hlbl_tooltip is not None:
            self._hlbl_tooltip.hide()
        super().leaveEvent(event)

    def toolTip(self) -> str:
        return "" if self._hlbl_tooltip is None else self._hlbl_tooltip.text()

    def setToolTip(self, label: str):
        if self._hlbl_tooltip is None:
            self._hlbl_tooltip = QHoverLabel(label, self)
            self._hlbl_tooltip.hide()
        else:
            self._hlbl_tooltip.setText(label)
