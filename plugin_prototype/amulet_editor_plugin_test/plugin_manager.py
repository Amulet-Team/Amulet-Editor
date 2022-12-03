from __future__ import annotations

import json
import logging
import os.path
from os.path import relpath, normpath
from typing import TYPE_CHECKING, Optional, List, NamedTuple, Iterable, Type
import weakref
from enum import IntEnum
import glob
import importlib.util
import sys
import traceback
import re
from collections import UserDict
from copy import copy
from abc import ABC, abstractmethod
from threading import RLock
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from PySide6.QtCore import Signal, QObject

from .thread import InvokeMethod

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


class PluginUID(NamedTuple):
    identifier: str  # The package name. This is the name used when importing the package. Eg "my_name_my_plugin". This must be a valid python identifier.
    version: Version  # The version number of the plugin.

    def to_string(self):
        return f"{self.identifier}@{self.version}"

    @classmethod
    def from_string(cls, s: str):
        match = re.fullmatch(r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)@(?P<version>.*)", s)
        if match is None:
            raise ValueError(f"Invalid PluginUID string: {s}")
        version = Version(match.group("version"))
        return cls(match.group("identifier"), version)


RequirementPattern = re.compile(r"(?P<identifier>[a-zA-Z_]+[a-zA-Z_0-9]*)(?P<requirement>.*)")


class PluginRequirement(NamedTuple):
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
        return item.identifier == self.plugin_identifier and item.version in self.specifier


class PluginState(IntEnum):
    Disabled = 0  # Plugin is not enabled by the user
    Inactive = (
        1  # Plugin is enabled by the user but had dependencies that are not enabled
    )
    Enabled = 2  # Plugin is fully enabled


class PluginData(NamedTuple):
    """Static, publicly accessible data about a plugin"""
    uid: PluginUID  # The unique identifier for the plugin. Made up of the plugin id and the version number. No two plugins may have the same UID.
    path: str  # The root path of the plugin.
    name: str  # The public name of the plugin.
    depends: tuple[PluginRequirement, ...]  # The plugins that this plugin depends on. This plugin will only be loaded once these plugins have been loaded.


_plugin_classes: dict[int, Type[PluginContainer]] = {}


def _plugin_class(cls: Type[PluginContainer]):
    if cls.FormatVersion in _plugin_classes:
        raise ValueError(f"Two classes have been registered with format version {cls.FormatVersion}")
    _plugin_classes[cls.FormatVersion] = cls


class PluginContainer(ABC):
    data: PluginData
    instance: Optional[Plugin]  # The instance of the plugin.
    state: PluginState

    @classmethod
    @property
    @abstractmethod
    def FormatVersion(cls) -> int:
        raise NotImplementedError

    def __init__(self, data: PluginData):
        self.data = data
        self.instance = None
        self.state = PluginState.Disabled

    @classmethod
    def from_path(cls, plugin_path: str) -> PluginContainer:
        """
        Populate a PluginContainer instance from the data in a directory.
        plugin_path is the system path to a directory containing a plugin.json file.
        """
        with open(os.path.join(plugin_path, "plugin.json")) as f:
            plugin_data = json.load(f)
        if not isinstance(plugin_data, dict):
            raise TypeError("plugin.json must be a dictionary.")

        # Get the plugin identifier
        format_version = plugin_data.get("format_version", 1)
        if not isinstance(format_version, int):
            raise TypeError("plugin.json[format_version] must be an int")
        try:
            cls2 = _plugin_classes[format_version]
        except KeyError:
            raise ValueError(f"Unknown plugin format version {format_version}")
        else:
            return cls2.from_data(plugin_path, plugin_data)

    @classmethod
    @abstractmethod
    def from_data(cls, plugin_path: str, plugin_data: dict) -> PluginContainer:
        raise NotImplementedError


@_plugin_class
class PluginContainerV1(PluginContainer):
    FormatVersion = 1

    @classmethod
    def from_data(cls, plugin_path: str, plugin_data: dict) -> PluginContainerV1:
        """
        Populate a PluginContainer instance from the data in a directory.
        plugin_path is the system path to a directory containing a plugin.json file.
        """
        # Get the plugin identifier
        plugin_identifier = plugin_data.get("identifier")
        if not isinstance(plugin_identifier, str):
            raise TypeError("plugin.json[identifier] must be a string")
        if not plugin_identifier.isidentifier():
            raise ValueError("plugin.json[identifier] must be a valid python identifier")

        # Get the plugin version
        plugin_version_string = plugin_data.get("version")
        if not isinstance(plugin_version_string, str):
            raise TypeError("plugin.json[version] must be a PEP 440 version string")
        plugin_version = Version(plugin_version_string)

        # Get the plugin name
        plugin_name = plugin_data.get("name")
        if not isinstance(plugin_version_string, str):
            raise TypeError("plugin.json[name] must be a string")

        # Get the plugin dependencies
        depends: list[str] = plugin_data.get("depends", [])
        if not isinstance(depends, list) and all(
                isinstance(d, str) for d in depends
        ):
            raise TypeError(
                "plugin.json[depends] must be a list of string identifiers and version specifiers if defined.\nEg. [\"plugin_1 ~=1.0\", \"plugin_2 ~=1.3\"]"
            )

        parsed_depends = tuple(map(PluginRequirement.from_string, depends))

        return cls(
            PluginData(
                PluginUID(plugin_identifier, plugin_version),
                plugin_path,
                plugin_name,
                parsed_depends,
            )
        )


PluginConfig = dict[str, bool]
PluginConfigPath = "plugins.json"


class PluginManager(QObject):
    __plugins: dict[PluginUID, PluginContainer]
    __plugins_config: PluginConfig

    def __init__(self, api: AppPrivateAPI):
        super().__init__()
        self.__api = weakref.ref(api)
        self.__plugins = {}
        self.__plugins_config = {}
        self.__lock = RLock()

    def init(self):
        self.__load_plugin_config()
        self.__find_plugins()

    @property
    def api(self) -> AppPrivateAPI:
        return self.__api()

    def __load_plugin_config(self):
        with self.__lock:
            try:
                plugin_config: PluginConfig
                with open(PluginConfigPath) as f:
                    plugin_config = json.load(f)
                if not isinstance(plugin_config, dict) and all(isinstance(v, bool) for v in plugin_config.values()):
                    raise TypeError
            except (FileNotFoundError, json.JSONDecodeError, TypeError):
                plugin_config = {}
            self.__plugins_config = plugin_config

    def __save_plugin_config(self):
        with self.__lock:
            with open(PluginConfigPath, "w") as f:
                json.dump(self.__plugins_config, f)

    def __find_plugins(self):
        """find and populate plugins"""
        with self.__lock:
            for plugin_dir in PluginDirs:
                for manifest_path in glob.glob(
                    os.path.join(plugin_dir, "*", "plugin.json")
                ):
                    try:
                        plugin_path = os.path.dirname(manifest_path)
                        plugin_container = PluginContainer.from_path(plugin_path)
                        plugin_uid = plugin_container.data.uid

                        # Ensure that the module name does not shadow an existing module
                        try:
                            mod = importlib.import_module(plugin_uid.identifier)
                        except ModuleNotFoundError:
                            # No module with this name. We are all good
                            pass
                        else:
                            # Imported a module with this name
                            if plugin_path != mod.__path__[0] if hasattr(mod, "__path__") else plugin_path != os.path.splitext(mod.__file__)[0]:
                                # If the path does not match the expected path then it shadows an existing module
                                log.warning(f"Skipping {plugin_container.data.path} because it would shadow module {plugin_uid.identifier}.")
                                continue

                        if plugin_uid not in self.__plugins:
                            self.__plugins[plugin_uid] = plugin_container
                        elif self.__plugins[plugin_uid].data.path != plugin_path:
                            log.warning(
                                f"Two plugins cannot have the same identifier and version.\n{self.__plugins[plugin_uid].data.path} and {plugin_path} have the same identifier and version."
                            )
                    except Exception as e:
                        log.exception(e)

            for plugin_str, enabled in self.__plugins_config.items():
                plugin_uid = PluginUID.from_string(plugin_str)
                if enabled and plugin_uid in self.__plugins:
                    try:
                        self.enable_plugin(plugin_uid)
                    except Exception as e:
                        log.exception(e)

    def enable_plugin(self, plugin_uid: PluginUID):
        """Enable a plugin

        :param plugin_uid: The unique identifier of the plugin to enable
        :raises: Exception if an error happened when loading the plugin.
        """
        with self.__lock:
            if not isinstance(plugin_uid, PluginUID):
                raise TypeError
            plugin_container = self.__plugins[plugin_uid]
            if plugin_container.state is not PluginState.Disabled:
                # Cannot enable a plugin that is not currently disabled.
                return
            if all(
                any(uid in requirement and plugin.state is PluginState.Enabled for uid, plugin in self.__plugins.items())
                for requirement in plugin_container.data.depends
            ):
                # all dependencies are already satisfied so the plugin can be enabled.
                self.__load_plugin(plugin_container)
                self._recursive_enable_plugins()
            else:
                # at least one dependency has not been enabled yet.
                # Put this on the to-do list until its dependencies are enabled.
                self.__set_plugin_state(plugin_container, PluginState.Inactive)

    def __load_plugin(self, plugin_container: PluginContainer):
        """Import and load a plugin."""
        with self.__lock:
            path = plugin_container.data.path
            if os.path.isdir(path):
                path = os.path.join(path, "__init__.py")
            spec = importlib.util.spec_from_file_location(
                plugin_container.data.uid.identifier, path
            )
            if spec is None:
                raise Exception
            mod = importlib.util.module_from_spec(spec)
            if mod is None:
                raise Exception
            sys.modules[plugin_container.data.uid.identifier] = mod
            spec.loader.exec_module(mod)

            def init_plugin():
                # User code must be run from the main thread to avoid issues.
                plugin_container.instance = mod.Plugin(self.api)
                plugin_container.instance.on_load()

            print("start")
            InvokeMethod(init_plugin)
            print("finished")
            self.__set_plugin_state(plugin_container, PluginState.Enabled)

    def _recursive_enable_plugins(self):
        """Enable all inactive plugins that can be enabled until no more can be."""
        with self.__lock:
            enabled_count = -1
            while enabled_count:
                enabled_count = 0
                for plugin_container in list(self.__plugins.values()):
                    if plugin_container.state is PluginState.Inactive and all(
                        any(uid in requirement and plugin.state is PluginState.Enabled for uid, plugin in self.__plugins.items())
                        for requirement in plugin_container.data.depends
                    ):
                        # all dependencies are satisfied so the plugin can be enabled.
                        try:
                            self.__load_plugin(plugin_container)
                        except Exception as e:
                            log.exception(e)
                        else:
                            enabled_count += 1

    def disable_plugin(self, plugin_uid: PluginUID):
        """Disable a plugin and inactive all dependents."""
        with self.__lock:
            if not isinstance(plugin_uid, PluginUID):
                raise TypeError
            plugin_container = self.__plugins[plugin_uid]
            if plugin_container.state is PluginState.Disabled:
                # Cannot disable a plugin that is already disabled
                return
            elif plugin_container.state is PluginState.Enabled:
                self.__unload_plugin(plugin_container)
            self.__set_plugin_state(plugin_container, PluginState.Disabled)

    def __unload_plugin(self, plugin_container: PluginContainer):
        """Unload and destroy a plugin."""
        with self.__lock:
            self._recursive_inactive_plugins(plugin_container.data.uid)
            try:
                print("start")
                InvokeMethod(plugin_container.instance.on_unload)
                print("finished")
            except Exception as e:
                log.exception(e, exc_info=e)
            plugin_container.instance = None
            sys.modules.pop(plugin_container.data.uid.identifier, None)

    def _recursive_inactive_plugins(self, plugin_uid: PluginUID):
        """
        Recursively inactive all dependents of a plugin.
        When a plugin is disabled none of its dependents are valid any more so they must be inactivated.

        :param plugin_uid: The plugin unique identifier to find dependents of.
        """
        with self.__lock:
            for plugin_container in self.__plugins.values():
                if (
                    plugin_container.state is PluginState.Enabled
                    and any(plugin_uid in requirement for requirement in plugin_container.data.depends)
                ):
                    self.__unload_plugin(plugin_container)
                    self.__set_plugin_state(plugin_container, PluginState.Inactive)

    def get_plugin(self, plugin_identifier: str) -> Plugin:
        """
        Get the instance of a plugin.
        Do not store other plugin instances.
        Useful to use the API of another plugin.
        """
        with self.__lock:
            plugin = next((p for p in self.__plugins.values() if p.data.uid.identifier == plugin_identifier and p.state is PluginState.Enabled), None)
            if plugin is None:
                raise KeyError(f"Plugin {plugin_identifier} has not been enabled.")
            return plugin.instance

    def __set_plugin_state(self, plugin_container: PluginContainer, plugin_state: PluginState):
        plugin_container.state = plugin_state
        self.__plugins_config[plugin_container.data.uid.to_string()] = bool(plugin_state)
        self.__save_plugin_config()
        self.plugin_state_change.emit(plugin_container.data.uid, plugin_container.state)

    plugin_state_change = Signal(PluginUID, PluginState)

    def iter_plugins(self) -> Iterable[tuple[PluginData, PluginState]]:
        """Iterate over all plugins regardless of enabled state."""
        return [(plugin.data, plugin.state) for plugin in self.__plugins.values()]
