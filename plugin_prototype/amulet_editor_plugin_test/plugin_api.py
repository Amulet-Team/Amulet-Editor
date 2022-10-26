from __future__ import annotations
from typing import TYPE_CHECKING, Type, Generator
import weakref
from PySide6.QtCore import Signal, QObject

from .plugin_manager import PluginManager, PluginUID, PluginState, PluginData

if TYPE_CHECKING:
    from .app import App
    from .view import View
    from .plugin import Plugin


class AppPrivateAPI(QObject):
    """
    This class represents the private API for the app.
    This API must only be accessible to the plugin core and the App.
    The Plugin interface and the App can expose parts of the API publicly.
    """

    def __init__(self, app: App):
        super().__init__()
        self.__app = weakref.ref(app)
        self.__plugin_manager = PluginManager(self)
        self.__plugin_manager.plugin_state_change.connect(self.plugin_state_change)

    def init(self):
        self.__plugin_manager.init()

    @property
    def app(self) -> App:
        return self.__app()

    def enable_plugin(self, plugin_uid: PluginUID):
        """Enable a plugin

        :param plugin_uid: The unique identifier of the plugin to enable
        :raises: Exception if an error happened when loading the plugin.
        """
        self.__plugin_manager.enable_plugin(plugin_uid)

    def disable_plugin(self, plugin_uid: PluginUID):
        """Disable a plugin and inactive all dependents."""
        self.__plugin_manager.disable_plugin(plugin_uid)

    plugin_state_change = Signal(PluginUID, PluginState)

    def iter_plugins(self) -> Generator[tuple[PluginData, PluginState], None, None]:
        """Iterate over all plugins regardless of enabled state."""
        yield from self.__plugin_manager.iter_plugins()

    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        return self.__plugin_manager.get_plugin(plugin_identifier)

    def register_view(self, plugin: Plugin, view_name: str, view: Type[View]):
        """Register a new view"""
        # this would be better split into a couple of functions
        raise NotImplementedError
