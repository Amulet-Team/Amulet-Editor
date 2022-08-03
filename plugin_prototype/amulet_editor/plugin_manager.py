import json
import logging
import os.path
from typing import TYPE_CHECKING, Optional, Any
import weakref
from enum import Enum
from dataclasses import dataclass
import glob

if TYPE_CHECKING:
    from .plugin import Plugin
    from .app import AppPrivateAPI

log = logging.getLogger(__name__)
PluginDirs = [
    os.path.abspath(
        os.path.join(__file__, "..", "..", "plugins")
    )  # TODO: set up a better plugin path
]


class PluginState(Enum):
    Disabled = 0  # Plugin is not enabled by the user
    Inactive = (
        1  # Plugin is enabled by the user but had dependencies that are not enabled
    )
    Enabled = 2  # Plugin is fully enabled


@dataclass
class PluginContainer:
    plugin_path: str
    plugin_identifier: str
    metadata: dict[str, Any]
    depends: list[str]
    plugin_instance: Optional[Plugin] = None
    plugin_state: PluginState = PluginState.Disabled


class PluginManager:
    __plugins: dict[str, PluginContainer]

    def __init__(self, api: AppPrivateAPI):
        self.__api = weakref.ref(api)
        self.__plugins = {}
        self.__find_plugins()
        self.__enable_plugins()

    @property
    def api(self) -> AppPrivateAPI:
        return self.__api()

    def __find_plugins(self):
        """find and populate plugins"""
        for plugin_dir in PluginDirs:
            for manifest_path in glob.glob(
                os.path.join(plugin_dir, "*", "plugin.json")
            ):
                try:
                    plugin_path = os.path.dirname(manifest_path)
                    with open(manifest_path) as f:
                        metadata = json.load(f)
                    if not isinstance(metadata, dict):
                        raise TypeError("plugin.json must be a dictionary.")
                    plugin_identifier = metadata["identifier"]
                    if not isinstance(plugin_identifier, str):
                        raise TypeError("plugin.json[identifier] must be a string")
                    if plugin_identifier in self.__plugins:
                        if self.__plugins[plugin_identifier].plugin_path == plugin_path:
                            continue
                        else:
                            raise ValueError(
                                f"Two plugins cannot have the same identifier. {self.__plugins[plugin_identifier].plugin_path} and {plugin_path} have the same identifier."
                            )

                    depends = metadata.get("depends", [])
                    if not isinstance(depends, list) and all(
                        isinstance(d, str) for d in depends
                    ):
                        raise TypeError(
                            "plugin.json[depends] must be a list of string identifiers if defined"
                        )
                    plugin_container = PluginContainer(
                        plugin_path,
                        plugin_identifier,
                        metadata,
                        depends,
                    )
                    self.__plugins[plugin_identifier] = plugin_container

                except Exception as e:
                    log.exception(str(e))

    def __enable_plugins(self):
        # load from a config file which plugins were enabled last session and enable them.
        # for simplicity, we are just going to enable all plugins
        for plugin_identifier in list(self.__plugins):
            self.enable_plugin(plugin_identifier)

    def __load_plugin(self, plugin_container: PluginContainer):
        """Import and load a plugin."""
        plugin_container.plugin_state = PluginState.Enabled
        raise NotImplementedError  # TODO: load the plugin class
        plugin_container.plugin_instance.on_load()

    def enable_plugin(self, plugin_identifier: str):
        """Enable a plugin"""
        plugin_container = self.__plugins[plugin_identifier]
        if plugin_container.plugin_state is not PluginState.Disabled:
            return
        if all(
            dep in self.__plugins
            and self.__plugins[dep].plugin_state is PluginState.Enabled
            for dep in plugin_container.depends
        ):
            # all dependencies are already satisfied so the plugin can be enabled.
            self.__load_plugin(plugin_container)
            self._recursive_enable_plugins()
        else:
            # at least one dependency has not been enabled yet.
            # Put this on the to-do list until its dependencies are enabled.
            plugin_container.plugin_state = PluginState.Inactive

    def _recursive_enable_plugins(self):
        """Enable all inactive plugins that can be enabled until no more can be."""
        enabled_count = -1
        while enabled_count:
            enabled_count = 0
            for plugin_container in list(self.__plugins.values()):
                if plugin_container.plugin_state is PluginState.Inactive and all(
                    dep in self.__plugins
                    and self.__plugins[dep].plugin_state is PluginState.Enabled
                    for dep in plugin_container.depends
                ):
                    # all dependencies are satisfied so the plugin can be enabled.
                    self.__load_plugin(plugin_container)
                    enabled_count += 1

    def __unload_plugin(self, plugin_container: PluginContainer):
        """Unload and destroy a plugin."""
        self._recursive_inactive_plugins(plugin_container.plugin_identifier)
        try:
            plugin_container.plugin_instance.on_unload()
        except Exception as e:
            log.exception(e, exc_info=e)
        plugin_container.plugin_instance = None

    def disable_plugin(self, plugin_identifier: str):
        """Disable a plugin and inactive all dependents."""
        plugin_container = self.__plugins[plugin_identifier]
        if plugin_container.plugin_state is PluginState.Enabled:
            self.__unload_plugin(plugin_container)
        plugin_container.plugin_state = PluginState.Disabled

    def _recursive_inactive_plugins(self, plugin_identifier: str):
        """
        Recursively inactive all dependents of a plugin.
        When a plugin is disabled none of its dependents are valid any more so they must be inactivated.

        :param plugin_identifier: The plugin identifier to find dependents of.
        """
        for plugin_container in self.__plugins.values():
            if (
                plugin_container.plugin_state is PluginState.Enabled
                and plugin_identifier in plugin_container.depends
            ):
                self.__unload_plugin(plugin_container)
                plugin_container.plugin_state = PluginState.Inactive

    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        if (
            plugin_identifier in self.__plugins
            and self.__plugins[plugin_identifier].plugin_state is PluginState.Enabled
        ):
            return self.__plugins[plugin_identifier].plugin_instance
        else:
            raise KeyError("The requested plugin has not been enabled.")
