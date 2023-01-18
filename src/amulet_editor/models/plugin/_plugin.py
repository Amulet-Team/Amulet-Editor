from __future__ import annotations

from typing import Optional, Type, TypeVar

from runtime_final import final

from ._api import PluginAPI


"""
Rules for plugin developers.
1) You must use weakref.proxy if you store the plugin instance. Not doing so will crash the program when stopping the plugin.
"""


PluginAPIT = TypeVar("PluginAPIT", bound=PluginAPI)


class Plugin:
    """
    This is the base class for all plugins.
    To implement your own plugin, you must subclass and extend this class.
    The methods and attributes in this class are private to the plugin.
    The methods documented below are used by the plugin engine to drive the plugin.
    The permissions of each method are documented with the method.

    Functions and attributes can be exposed to other plugins via the PluginAPI class.
    Subclass PluginAPI and overwriting APIClass will change the API used by the plugin.
    """

    __api: Optional[PluginAPI]
    # The plugin API class to use. Plugins may overwrite this to change the API class.
    APIClass: Type[PluginAPI] = PluginAPI

    @final
    def __init__(self):
        self.__api = None
        self.on_init()
        self.public_api  # noqa

    def on_init(self):
        """
        Initialise default attributes.
        The plugin has not been enabled at this point.
        Plugins may override this method but must not call it.
        """
        pass

    def on_start(self):
        """
        Logic run when the plugin is started.
        All dependencies will be started when this is called.
        Plugins may override this method but must not call it.
        """
        pass

    def on_stop(self):
        """
        Logic run when the plugin is stopped.
        Dependents will be stopped at this point but dependencies are not.
        This must leave the program in the same state as it was before on_start was called.
        Plugins may override this method but must not call it.
        """
        pass

    @final
    def get_plugin(self, plugin_cls: Type[PluginAPIT]) -> PluginAPIT:
        """
        Get the public API for a plugin.
        Plugins must not store the returned object.
        """
        raise NotImplementedError

    @final
    @property
    def public_api(self) -> PluginAPI:
        """
        The public API for this plugin.
        Defaults to a blank API.
        Overwrite APIClass class variable with a subclass of PluginAPI to change the class that is used.
        """
        if self.__api is None:
            api_class = self.APIClass
            if not issubclass(api_class, PluginAPI):
                raise TypeError("APIClass must be a subclass of PluginAPI")
            self.__api = api_class(self)
        return self.__api
