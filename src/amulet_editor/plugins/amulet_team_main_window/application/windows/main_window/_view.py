from __future__ import annotations
from typing import Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from amulet_team_main_window.models.view import View


ViewType = Union[QWidget, View]


class ViewContainer(QWidget):
    """A widget to contain a View"""

    # In its basic form this could be implemented with a stacked widget
    # but I would like to look into support for multiple active views
    # and the ability to move views around hence the need for a container

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        f: Qt.WindowType = Qt.WindowType.Widget,
    ):
        super().__init__(parent, f)
        self._uid = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._view: Optional[ViewType] = None

    @property
    def view_cls(self) -> Optional[str]:
        return self._view.__class__

    def get_view(self) -> Optional[ViewType]:
        return self._view

    def swap_view(self, view: ViewType) -> Optional[ViewType]:
        """
        Swap the contained view.
        This orphans and returns the old view.
        It is the job of the caller to either hide and store it for later use or destroy it.

        :param view: The view instance to set. This must be an instance of QWidget or a subclass of QWidget and View.
        :return: The old orphaned view instance.
        """
        if not isinstance(view, View):
            raise TypeError("view must be an instance of View")
        if not isinstance(view, QWidget):
            raise TypeError("view must be an instance of QWidget")
        if view.parent() is not None:
            raise RuntimeError("view must be an orphan.")

        old_view = self._view
        if old_view is not None:
            old_view.disable_view()
            self._layout.removeWidget(old_view)
            # Orphan the widget
            old_view.setParent(None)
        self._view = view
        self._layout.addWidget(view)
        return old_view
