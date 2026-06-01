from PySide6.QtCore import QSize, Qt, QEvent, QCoreApplication
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QVBoxLayout, QPushButton
from PySide6.QtSvgWidgets import QSvgWidget

from amulet.app.exception import CatchExceptionDialog

from ._hover_label import HoverLabel


class SVGButton(QPushButton):
    """A QPushButton containing a stylable icon."""

    def __init__(self, icon_path: str) -> None:
        super().__init__()
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
        name: str | tuple[str, str, str | None],
        icon_path: str,
    ) -> None:
        super().__init__(icon_path)
        self._name = name
        self._tooltip: HoverLabel | None = None

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        with CatchExceptionDialog("Error localising ToolbarButton."):
            name = self._name
            if not isinstance(name, str):
                context, key, disambiguation = self._name
                name = QCoreApplication.translate(context, key, disambiguation)
            if self._tooltip is not None:
                self._tooltip.setText(name)

    def show_tooltip(self) -> None:
        if self._tooltip is None:
            self._tooltip = HoverLabel(self)
            self._localise()
        self._tooltip.show()

    def hide_tooltip(self) -> None:
        if self._tooltip is not None:
            self._tooltip.hide()
