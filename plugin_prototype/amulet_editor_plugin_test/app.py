from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Type

from .plugin_manager import PluginManager

if TYPE_CHECKING:
    from .plugin import Plugin
    from .view import View


class AppPrivateAPI:
    """
    This class represents the private API for the app.
    This API must only be accessible to the plugin core and the App.
    The Plugin interface and the App can expose parts of the API publicly.
    """

    def __init__(self, app: App):
        self.__app = weakref.ref(app)
        self.plugin_manager = PluginManager(self)

    def init(self):
        self.plugin_manager.init()

    @property
    def app(self) -> App:
        return self.__app()

    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        return self.plugin_manager.get_plugin(plugin_identifier)

    def register_view(self, plugin: Plugin, view_name: str, view: Type[View]):
        """Register a new view"""
        # this would be better split into a couple of functions
        raise NotImplementedError


class App:
    """The Qt App class"""

    def __init__(self):
        self.__api = AppPrivateAPI(self)

    def exc(self):
        self.__api.init()
