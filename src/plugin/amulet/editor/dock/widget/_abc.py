from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget


class DockWidget(QWidget):
    """A base class for all widgets in the docking system."""

    @property
    def title(self) -> str:
        """The title to display in the tab."""
        return ""

    # Emit this signal to notify that the title has changed
    title_changed = Signal(str)

    @property
    def icon(self) -> QIcon:
        """The icon to display in the tab."""
        return QIcon()

    # Emit this signal to notify that the icon has changed
    icon_changed = Signal(QIcon | None)
