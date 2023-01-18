from __future__ import annotations
from typing import Type, Callable

from ._landing_window import Ui_AmuletLandingWindow
from ._view import ViewContainer, View


# Terminology
# A tool button is a button in the toolbar
# A view is a program that exists within Amulet
# A view container is an object that can contain a view

UID = str


class AmuletMainWindow(Ui_AmuletLandingWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._view_constructors: dict[UID, Type[View]] = {}
        self._view_containers: list[ViewContainer] = [self._view_container]
        self._active_view = self._view_container
        self._orphan_views: dict[UID, list[View]] = {}

    def activate_view(self, view_uid: UID):
        """
        Enable a view registered to the given identifier.
        If a view of this type already exists it will be activated otherwise a new view will be created in the active container.

        :param view_uid: The unique identifier to enable
        """
        if view_uid not in self._view_constructors:
            raise ValueError(f"There is no view registered to view_uid {view_uid}")

        # Scan the view containers to see if a view of this type already exists
        for existing_view in self._view_containers:
            if existing_view.view_uid == view_uid:
                break
        else:
            existing_view = None

        if existing_view is None:
            # Replace the active view
            view = self._view_constructors[view_uid]()
            old_view = self._view_container.swap_view(view_uid, view)
            # TODO: implement view caching
            if old_view is not None:
                old_view.deleteLater()
        else:
            existing_view.get_view().activate_view()

        self._toolbar.activate(view_uid)

    def register_view(self, uid: UID, icon: str, name: str, view: Type[View]):
        """
        Register a callback for when a view is activated.

        :param uid: The unique identifier of the view.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param view: A function that has no inputs and returns a View instance.
        """
        if not issubclass(view, View):
            raise TypeError("view must be a subclass of View")
        if uid in self._view_constructors:
            raise ValueError(f"uid {uid} has already been registered.")
        self._view_constructors[uid] = view
        self._toolbar.add_dynamic_button(
            uid, icon, name, lambda: self.activate_view(uid)
        )

    def add_button(
        self, uid: str, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add an icon to the toolbar.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_dynamic_button(uid, icon, name, callback)

    def add_static_button(
        self, uid: str, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add a static icon to the toolbar.
        These should be reserved for special cases.
        Third party plugins should use :meth:`add_button`.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_static_button(uid, icon, name, callback)
