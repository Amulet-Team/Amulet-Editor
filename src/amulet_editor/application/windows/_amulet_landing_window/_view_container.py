from __future__ import annotations
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ViewContainer(QWidget):
    # In its basic form this could be implemented with a stacked widget
    # but I would like to look into support for multiple active views
    # and the ability to move views around hence the need for a container

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        f: Qt.WindowFlags = Qt.WindowFlags(),
    ):
        super().__init__(parent, f)
        self._uid = None
        self._layout = QVBoxLayout(self)

    def set_view(self, view: QWidget):
        for _ in range(self._layout.count()):
            # Orphan the widget
            widget = self._layout.itemAt(0).widget()
            widget.setParent(None)
            # TODO: perhaps let the widget handle this. Some plugins may want to cache the widget for later
            widget.deleteLater()

        self._layout.addWidget(view)
