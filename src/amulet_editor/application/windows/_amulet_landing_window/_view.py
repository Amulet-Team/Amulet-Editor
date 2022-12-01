from __future__ import annotations
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout


class View(QWidget):
    def on_remove(self):
        """
        Called when the view is removed from a view container.
        Default behaviour is to destroy the view but you may wish to store this to reload it in the future.
        """
        self.deleteLater()


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

    def set_view(self, view: View):
        for _ in range(self._layout.count()):
            # Orphan the widget
            widget: View = self._layout.itemAt(0).widget()
            widget.setParent(None)
            widget.on_remove()

        self._layout.addWidget(view)
