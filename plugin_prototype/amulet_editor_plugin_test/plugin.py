from __future__ import annotations

from typing import TYPE_CHECKING, Type
import weakref

if TYPE_CHECKING:
    from .app import AppPrivateAPI
    from .view import View

from ._final import final


class Plugin:
    # Plugin identifiers for other plugins that must be loaded before this plugin
    PluginDepends: list[str] = []

    @final
    def __init__(self, api: AppPrivateAPI):
        self.__api = weakref.ref(api)

    def on_load(self):
        """
        Logic run when the plugin is enabled.
        All dependencies will be enabled when this is called.
        """
        pass

    def on_unload(self):
        """
        Logic run when the plugin is disabled.
        Dependents will be unloaded at this point but dependencies are not.
        """
        pass

    @final
    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        return self.__api().get_plugin(plugin_identifier)

    @final
    def register_view(self, plugin: Plugin, view_name: str, view: Type[View]):
        """Register a new view"""
        # this would be better split into a couple of functions
        self.__api().register_view(self, view_name, view)
