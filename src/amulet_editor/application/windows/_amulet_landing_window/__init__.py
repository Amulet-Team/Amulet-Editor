from __future__ import annotations
from typing import final, Type, Callable

from PySide6.QtCore import Slot

from ._landing_window import Ui_AmuletLandingWindow
from .pages.settings import SettingsPage
from .views.home import HomeView
from ._view import ViewContainer, View


# Terminology
# A tool button is a button in the toolbar
# A view is a program that exists within Amulet
# A view container is an object that can contain a view

UID = str


class Plugin:
    @final
    def __init__(self, window: AmuletLandingWindow):
        # Temporary
        self.window = window

    def enable(self):
        pass

    def disable(self):
        pass


class HomePlugin(Plugin):
    def enable(self):
        self.window.register_view("amulet:home", "home.svg", "Home", HomeView)


class SettingsPlugin(Plugin):
    _windows: list

    def enable(self):
        self._windows = []
        self.window.private_add_button("amulet:settings", "settings.svg", "Settings", self._on_click)

    def _on_click(self):
        settings = SettingsPage()
        settings.showNormal()
        self._windows.append(settings)


class AmuletLandingWindow(Ui_AmuletLandingWindow):
    def __init__(self):
        super().__init__()

        self._views: dict[UID, Type[View]] = {}
        # TODO: improve this to support multiple view containers
        self._orphan_views: dict[UID, list[View]] = {}

        # Load plugins
        self.home = HomePlugin(self)
        self.home.enable()
        self.settings = SettingsPlugin(self)
        self.settings.enable()
        self.activate_view("amulet:home")

    def activate_view(self, uid: UID):
        """
        Enable a view registered to the given identifier.
        If a view of this type already exists it will be activated otherwise a new view will be created in the active container.

        :param uid: The unique identifier to enable
        """
        if uid not in self._views:
            raise ValueError(f"There is no view registered to uid {uid}")
        # TODO: check if a view of this type exists
        view = self._views[uid]()
        self._view_container.set_view(view)
        self._toolbar.activate(uid)

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
        if uid in self._views:
            raise ValueError(f"uid {uid} has already been registered.")
        self._views[uid] = view
        self._toolbar.add_dynamic_button(uid, icon, name, lambda: self.activate_view(uid))

    def add_button(self, uid: str, icon: str, name: str, callback: Callable[[], None] = None):
        """
        Add an icon to the toolbar.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_dynamic_button(uid, icon, name, callback)

    def private_add_button(self, uid: str, icon: str, name: str, callback: Callable[[], None] = None):
        """
        Add an icon to the toolbar.

        :param uid: The unique identifier of the button.
        :param icon: The icon path to use in the toolbar.
        :param name: The name of the view to use in the icon tooltip.
        :param callback: The function to call when the button is clicked.
        :return:
        """
        self._toolbar.add_static_button(uid, icon, name, callback)
