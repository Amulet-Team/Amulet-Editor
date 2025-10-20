from amulet.app.resource import get_resource_path
from plugin.amulet.editor._label import QHoverLabel
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import (
    QEnterEvent,
    QPixmap,
    QIcon,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtSvgWidgets import QSvgWidget


class SVGButton(QPushButton):
    """A QPushButton containing a stylable icon."""

    def __init__(
        self,
        icon_path: str = get_resource_path("icons/tabler/question-mark.svg"),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon = QSvgWidget(icon_path)
        self._layout.addWidget(self._icon)

    def setIcon(self, icon: str | QIcon | QPixmap) -> None:
        if isinstance(icon, str):
            self._icon.load(icon)
        else:
            raise TypeError

    def setIconSize(self, size: QSize) -> None:
        self._icon.setFixedSize(size)


class ToolbarButton(SVGButton):
    def __init__(
        self,
        icon_path: str = get_resource_path("icons/tabler/question-mark.svg"),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(icon_path, parent)
        self._hlbl_tooltip: QHoverLabel | None = None

    def enterEvent(self, event: QEnterEvent) -> None:
        if self._hlbl_tooltip is not None and len(self._hlbl_tooltip.text()) > 0:
            self._hlbl_tooltip.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._hlbl_tooltip is not None:
            self._hlbl_tooltip.hide()
        super().leaveEvent(event)

    def toolTip(self) -> str:
        return "" if self._hlbl_tooltip is None else self._hlbl_tooltip.text()

    def setToolTip(self, label: str) -> None:
        if self._hlbl_tooltip is None:
            self._hlbl_tooltip = QHoverLabel(label, self)
            self._hlbl_tooltip.hide()
        else:
            self._hlbl_tooltip.setText(label)
