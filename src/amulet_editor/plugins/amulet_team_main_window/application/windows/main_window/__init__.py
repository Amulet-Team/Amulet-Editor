from __future__ import annotations
from typing import Type, Callable, TYPE_CHECKING
from uuid import uuid4

from PySide6.QtGui import QShortcut
from PySide6.QtCore import Qt

from ._landing_window import Ui_AmuletLandingWindow
from ._view import ViewContainer, View

from amulet_team_inspector import show_inspector

if TYPE_CHECKING:
    from amulet_editor.models.widgets._toolbar import AToolBar


# Terminology
# A tool button is a button in the toolbar
# A view is a program that exists within Amulet
# A view container is an object that can contain a view


UID = UUID = str


class AmuletMainWindow(Ui_AmuletLandingWindow):
    _toolbar: AToolBar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._view_classes: dict[Type[View], UUID] = {}
        self._view_containers: list[ViewContainer] = [self._view_container]
        self._active_view = self._view_container
        f12 = QShortcut(Qt.Key.Key_F12, self)
        f12.activated.connect(show_inspector)

    def activate_view(self, view_cls: Type[View]):
        """
        Enable a view registered to the given identifier.
        If a view of this type already exists it will be activated otherwise a new view will be created in the active container.

        :param view_cls: The view type to enable
        """
        if view_cls not in self._view_classes:
            raise ValueError(f"View type {view_cls} has not been registered")

        # Scan the view containers to see if a view of this type already exists
        for existing_view in self._view_containers:
            if existing_view.view_cls is view_cls:
                break
        else:
            existing_view = None

        if existing_view is None:
            # Replace the active view
            view = view_cls()
            old_view = self._view_container.swap_view(view)
            # TODO: implement view caching
            if old_view is not None:
                old_view.deleteLater()
        else:
            existing_view.get_view().activate_view()

        self._toolbar.activate(self._view_classes[view_cls])

    def register_view(self, view_cls: Type[View], icon: str, name: str):
        """
        Register a view class for this window only. This adds a button to activate the view.

        :param view_cls: The view class to register.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        """
        if not issubclass(view_cls, View) or view_cls is View:
            raise TypeError("view must be a subclass of View")
        if view_cls in self._view_classes:
            raise ValueError(f"View type {view_cls} has already been registered.")
        self._view_classes[view_cls] = uid = str(uuid4())
        self._toolbar.add_dynamic_button(
            uid, icon, name, lambda: self.activate_view(view_cls)
        )

    def unregister_view(self, view_cls: Type[View]):
        """
        Unregister a view for this window only.

        :param view_cls: The view class to unregister.
        :return:
        """
        # TODO: raise NotImplementedError
        pass

    def add_toolbar_button(
        self, uid: UID, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add an icon to the toolbar for this window only.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_dynamic_button(uid, icon, name, callback)

    def add_static_toolbar_button(
        self, uid: UID, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add a static icon to the toolbar for this window only.
        These should be reserved for special cases.
        Third party plugins should use :meth:`add_button`.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_static_button(uid, icon, name, callback)

    def remove_toolbar_button(self, uid: UID):
        """
        Remove a toolbar button.

        :param uid: The unique identifier for the toolbar button to remove.
        :return:
        """
        self._toolbar.remove_button(uid)
