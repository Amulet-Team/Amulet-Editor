from __future__ import annotations

import json
import logging
import os.path
from os.path import relpath, normpath
from typing import TYPE_CHECKING, Optional, List
import weakref
from enum import Enum
from dataclasses import dataclass
import glob
import importlib.util
import sys
import traceback
import re
from collections import UserDict
from copy import copy
from packaging.version import Version
from packaging.specifiers import SpecifierSet

if TYPE_CHECKING:
    from .plugin import Plugin
    from .app import AppPrivateAPI

log = logging.getLogger(__name__)
PluginDirs = [
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "first_party_plugins")
    ),
    os.path.abspath(
        os.path.join(__file__, "..", "..", "plugins")
    )  # TODO: set up a better plugin path
]

TracePattern = re.compile(r"\s*File\s*\"(?P<path>.*?)\"")


def get_trace_paths() -> List[str]:
    return list(reversed([normpath(TracePattern.match(line).group("path")) for line in traceback.format_stack()]))[1:]


class CustomDict(UserDict):
    def __init__(self, original: dict):
        super().__init__()
        # self.data = original  # I would prefer to do this but getitem does not get called if this line is used instead.
        self.data = copy(original)

    def __getitem__(self, key):
        print(key)
        mod = super().__getitem__(key)
        try:
            module_path = normpath(mod.__file__)
            plugin_dir = next((path for path in PluginDirs if module_path.startswith(path)), None)
        except AttributeError:
            pass
        else:
            if plugin_dir is not None:
                plugin_dir = normpath(plugin_dir)
                plugin_path = os.path.join(plugin_dir, relpath(module_path, plugin_dir).split(os.sep)[0])
                for frame in get_trace_paths()[2:]:
                    if frame.startswith(plugin_path):
                        break
                    elif any(frame.startswith(path) for path in PluginDirs):
                        raise ImportError(
                            "Plugins cannot directly import other plugins. You must use the plugin API to iteract with other plugins.\n"
                            f"Plugin {frame} tried to import {key}"
                        )
        return mod


sys.modules = CustomDict(sys.modules)


@dataclass
class PluginUID:
    plugin_identifier: str  # The package name. This is the name used when importing the package. Eg "my_name_my_plugin". This must be a valid python identifier.
    version: Version  # The version number of the plugin.

    def __hash__(self):
        return hash((self.plugin_identifier, self.version))


RequirementPattern = re.compile(r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)(?P<requirement>.*)")


@dataclass
class PluginRequirement:
    plugin_identifier: str  # The package name
    specifier: SpecifierSet  # The version specifier. It is recommended to use the compatible format. Eg. "~=1.0"

    @classmethod
    def from_string(cls, requirement: str):
        match = RequirementPattern.fullmatch(requirement)
        if match is None:
            raise ValueError(f"\"{requirement}\" is not a valid requirement.\n It must be a python identifier followed by an optional PEP 440 compatible version specifier")
        specifier = SpecifierSet(match.group("requirement"))
        return cls(match.group("identifier"), specifier)

    def __contains__(self, item: PluginUID):
        if not isinstance(item, PluginUID):
            raise TypeError
        return item.plugin_identifier == self.plugin_identifier and item.version in self.specifier


class PluginState(Enum):
    Disabled = 0  # Plugin is not enabled by the user
    Inactive = (
        1  # Plugin is enabled by the user but had dependencies that are not enabled
    )
    Enabled = 2  # Plugin is fully enabled


@dataclass
class PluginContainer:
    plugin_path: str  # The root path of the plugin.
    plugin_uid: PluginUID  # The unique identifier for the plugin. Made up of the plugin id and the version number. No two plugins may have the same UID.
    depends: list[PluginRequirement]  # The plugins that this plugin depends on. This plugin will only be loaded once these plugins have been loaded.
    plugin_instance: Optional[Plugin] = None  # The instance of the plugin.
    plugin_state: PluginState = PluginState.Disabled

    @classmethod
    def from_path(cls, plugin_path: str) -> PluginContainer:
        """
        Populate a PluginContainer instance from the data in a directory.
        plugin_path is the system path to a directory containing a plugin.json file.
        """
        # Get and validate the plugin data
        with open(os.path.join(plugin_path, "plugin.json")) as f:
            metadata = json.load(f)
        if not isinstance(metadata, dict):
            raise TypeError("plugin.json must be a dictionary.")

        # Get the plugin identifier
        plugin_identifier = metadata.get("identifier")
        if not isinstance(plugin_identifier, str):
            raise TypeError("plugin.json[identifier] must be a string")
        if not plugin_identifier.isidentifier():
            raise ValueError("plugin.json[identifier] must be a valid python identifier")

        # Get the plugin version
        plugin_version_string = metadata.get("version")
        if not isinstance(plugin_version_string, str):
            raise TypeError("plugin.json[version] must be a PEP 440 version string")
        plugin_version = Version(plugin_version_string)

        # Get the plugin dependencies
        depends: list[str] = metadata.get("depends", [])
        if not isinstance(depends, list) and all(
            isinstance(d, str) for d in depends
        ):
            raise TypeError(
                "plugin.json[depends] must be a list of string identifiers and version specifiers if defined.\nEg. [\"plugin_1 ~=1.0\", \"plugin_2 ~=1.3\"]"
            )

        parsed_depends = list(map(PluginRequirement.from_string, depends))

        return PluginContainer(
            plugin_path,
            PluginUID(plugin_identifier, plugin_version),
            parsed_depends,
        )


class PluginManager:
    __plugins: dict[PluginUID, PluginContainer]

    def __init__(self, api: AppPrivateAPI):
        self.__api = weakref.ref(api)
        self.__plugins = {}

    def init(self):
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
                    plugin_container = PluginContainer.from_path(plugin_path)
                    plugin_uid = plugin_container.plugin_uid

                    if plugin_uid not in self.__plugins:
                        self.__plugins[plugin_uid] = plugin_container
                    elif self.__plugins[plugin_uid].plugin_path == plugin_path:
                        continue
                    else:
                        raise ValueError(
                            f"Two plugins cannot have the same identifier and version.\n{self.__plugins[plugin_uid].plugin_path} and {plugin_path} have the same identifier and version."
                        )

                except Exception as e:
                    log.exception(str(e))

    def __enable_plugins(self):
        # load from a config file which plugins were enabled last session and enable them.
        # for simplicity, we are just going to enable all plugins
        for plugin_identifier in list(self.__plugins):
            try:
                self.enable_plugin(plugin_identifier)
            except Exception as e:
                log.exception(e)

    def __load_plugin(self, plugin_container: PluginContainer):
        """Import and load a plugin."""
        plugin_container.plugin_state = PluginState.Enabled
        path = plugin_container.plugin_path
        if os.path.isdir(path):
            path = os.path.join(path, "__init__.py")
        spec = importlib.util.spec_from_file_location(
            plugin_container.plugin_uid.plugin_identifier, path
        )
        if spec is None:
            raise Exception
        mod = importlib.util.module_from_spec(spec)
        if mod is None:
            raise Exception
        sys.modules[plugin_container.plugin_uid.plugin_identifier] = mod
        spec.loader.exec_module(mod)
        plugin_container.plugin_instance = mod.Plugin(self.api)
        plugin_container.plugin_instance.on_load()

    def enable_plugin(self, plugin_uid: PluginUID):
        """Enable a plugin

        :param plugin_uid: The unique identifier of the plugin to enable
        :raises: Exception if an error happened when loading the plugin.
        """
        if not isinstance(plugin_uid, PluginUID):
            raise TypeError
        plugin_container = self.__plugins[plugin_uid]
        if plugin_container.plugin_state is not PluginState.Disabled:
            return
        if all(
            any(uid in requirement and plugin.plugin_state is PluginState.Enabled for uid, plugin in self.__plugins.items())
            for requirement in plugin_container.depends
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
                    any(uid in requirement and plugin.plugin_state is PluginState.Enabled for uid, plugin in self.__plugins.items())
                    for requirement in plugin_container.depends
                ):
                    # all dependencies are satisfied so the plugin can be enabled.
                    try:
                        self.__load_plugin(plugin_container)
                    except Exception as e:
                        log.exception(e)
                    else:
                        enabled_count += 1

    def __unload_plugin(self, plugin_container: PluginContainer):
        """Unload and destroy a plugin."""
        self._recursive_inactive_plugins(plugin_container.plugin_uid)
        try:
            plugin_container.plugin_instance.on_unload()
        except Exception as e:
            log.exception(e, exc_info=e)
        plugin_container.plugin_instance = None
        sys.modules.pop(plugin_container.plugin_uid.plugin_identifier, None)

    def disable_plugin(self, plugin_uid: PluginUID):
        """Disable a plugin and inactive all dependents."""
        plugin_container = self.__plugins[plugin_uid]
        if plugin_container.plugin_state is PluginState.Enabled:
            self.__unload_plugin(plugin_container)
        plugin_container.plugin_state = PluginState.Disabled

    def _recursive_inactive_plugins(self, plugin_uid: PluginUID):
        """
        Recursively inactive all dependents of a plugin.
        When a plugin is disabled none of its dependents are valid any more so they must be inactivated.

        :param plugin_uid: The plugin unique identifier to find dependents of.
        """
        for plugin_container in self.__plugins.values():
            if (
                plugin_container.plugin_state is PluginState.Enabled
                and any(plugin_uid in requirement for requirement in plugin_container.depends)
            ):
                self.__unload_plugin(plugin_container)
                plugin_container.plugin_state = PluginState.Inactive

    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        plugin = next((p for p in self.__plugins.values() if p.plugin_uid.plugin_identifier == plugin_identifier and p.plugin_state is PluginState.Enabled), None)
        if plugin is None:
            raise KeyError(f"Plugin {plugin_identifier} has not been enabled.")
        return plugin.plugin_instance
