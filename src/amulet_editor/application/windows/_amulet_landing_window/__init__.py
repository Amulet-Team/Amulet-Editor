from __future__ import annotations
from typing import final, Callable

from PySide6.QtCore import Slot

from ._landing_window import Ui_AmuletLandingWindow
from .pages.settings import SettingsPage
from .pages.home import HomePage
from ._view_container import ViewContainer


# Terminology
# A tool button is a button in the toolbar
# A view is a program that exists within Amulet
# A view container is an object that can contain a view


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
        self.window.toolbar.add_dynamic_button("amulet:home", "home.svg", "Home", self._on_click)
        self.window.toolbar.add_dynamic_button("amulet:home2", "home-2.svg", "Home")
        self.window.register_view("amulet:home", self._enable_view)

    def _on_click(self):
        self._enable_view()

    def _enable_view(self):
        self.window.toolbar.activate("amulet:home")
        self.window.active_view_container.set_view(HomePage())


class SettingsPlugin(Plugin):
    _windows: list

    def enable(self):
        self._windows = []
        self.window.toolbar.add_static_button("amulet:settings", "settings.svg", "Settings", self._on_click)

    def _on_click(self):
        settings = SettingsPage()
        settings.showNormal()
        self._windows.append(settings)


class AmuletLandingWindow(Ui_AmuletLandingWindow):
    def __init__(self):
        super().__init__()

        self._views = {}

        # Load plugins
        self.home = HomePlugin(self)
        self.home.enable()
        self.settings = SettingsPlugin(self)
        self.settings.enable()
        self.enable_view("amulet:home")

    def register_view(self, uid: str, initialiser: Callable[[], None]):
        """
        Register a callback for when a view is activated.

        :param uid: The uid of the view.
        :param initialiser: A function to activate the view.
        """
        if uid in self._views:
            raise ValueError(f"uid {uid} has already been registered.")
        self._views[uid] = initialiser

    def enable_view(self, uid: str):
        """
        Enable a view registered to the given identifier.

        :param uid: The unique identifier to enable
        """
        self._views[uid]()

    @property
    def active_view_container(self) -> ViewContainer:
        """Get the view container that is currently active."""
        # There is currently only one view container so this is hard coded.
        return self._view_container
