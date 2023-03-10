from __future__ import annotations
from typing import Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout


class View:
    def activate_view(self):
        """
        Run every time the view is activated by code or by clicking the tool button associated with the view.
        :meth:`wake_view` will be called after if the view did not have focus.
        This is useful if the view wants to reset to a default state every time the tool button is clicked.
        """
        pass

    def wake_view(self):
        """
        This is run when the view gains focus.
        If the view was focused by clicking the associated tool button :meth:`activate_view` will be called first.
        Useful in combination with :meth:`sleep_view` to switch between a high and low processing mode.
        """
        pass

    def sleep_view(self):
        """
        This is run when the view looses focus.
        This is useful to put the view into a low processing mode.
        This method must leave the view in a state where it can be disabled or woken again.
        """
        pass

    def can_disable_view(self) -> bool:
        """
        Can the view be disabled.
        Return False if for some reason the view cannot be disabled.

        :return: True if the view can be disabled. False otherwise.
        """
        return True

    def disable_view(self):
        """
        This is run when a view is about to be removed from a view container.
        This gives the view a chance to do any cleaning up before it is removed and potentially destroyed.
        This method must leave the view in a state where it can be destroyed or activated again.
        """
        pass


ViewType = Union[QWidget, View]


class ViewContainer(QWidget):
    """A widget to contain a View"""

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
        self._view: Optional[ViewType] = None
        self._view_uid: Optional[str] = None

    @property
    def view_uid(self) -> Optional[str]:
        return self._view_uid

    def get_view(self) -> Optional[ViewType]:
        return self._view

    def swap_view(self, view_uid: str, view: ViewType) -> Optional[ViewType]:
        """
        Swap the contained view.
        This orphans and returns the old view.
        It is the job of the caller to either hide and store it for later use or destroy it.

        :param view_uid: The unique identifier associated with the view.
        :param view: The view instance to set. This must be an instance of QWidget or a subclass of QWidget and View.
        :return: The old orphaned view instance.
        """
        if not isinstance(view_uid, str):
            raise TypeError("view_uid must be a string")
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
