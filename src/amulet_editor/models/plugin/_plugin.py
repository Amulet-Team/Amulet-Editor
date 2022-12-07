from __future__ import annotations

from runtime_final import final


class Plugin:
    # Plugin identifiers for other plugins that must be loaded before this plugin
    PluginDepends: list[str] = []

    @final
    def __init__(self):
        self.on_init()

    def on_init(self):
        """
        Initialise default attributes.
        The plugin has not been enabled at this point.
        Plugins may override this method but must not call it.
        """
        pass

    def on_load(self):
        """
        Logic run when the plugin is enabled.
        All dependencies will be enabled when this is called.
        Plugins may override this method but must not call it.
        """
        pass

    @final
    def unload(self):
        """
        Unload a plugin and all of its components.
        Plugins must not override or call this method.
        """
        self.on_unload()
        # TODO: unregister any registered components

    def on_unload(self):
        """
        Logic run when the plugin is disabled.
        Dependents will be unloaded at this point but dependencies are not.
        Plugins may override this method but must not call it.
        """
        pass

    # @final
    # def get_plugin(self, plugin_identifier: str) -> Plugin:
    #     """
    #     Get the instance of a plugin.
    #     Do not store other plugin instances.
    #     Useful to use the API of another plugin.
    #     """
    #     return self.__api().get_plugin(plugin_identifier)
    #
    # @final
    # def register_view(self, plugin: Plugin, view_name: str, view: Type[View]):
    #     """Register a new view"""
    #     # this would be better split into a couple of functions
    #     self.__api().register_view(self, view_name, view)
