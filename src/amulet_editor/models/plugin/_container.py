from __future__ import annotations

import json
import os.path
from typing import Optional, Type, Protocol
from abc import ABC, abstractmethod
from packaging.version import Version

from amulet_editor.data.paths._plugin import first_party_plugin_directory
from ._data import PluginData
from ._state import PluginState
from ._requirement import PluginRequirement
from ._uid import PluginUID


_plugin_classes: dict[int, Type[PluginContainer]] = {}


class Plugin(Protocol):
    def on_start(self):
        """
        Logic run when the plugin is started.
        All dependencies will be started when this is called.
        Plugins may implement this method but must not call it.
        """
        ...

    def on_stop(self):
        """
        Logic run when the plugin is stopped.
        Dependents will be stopped at this point but dependencies are not.
        This must leave the program in the same state as it was before on_start was called.
        Plugins may implement this method but must not call it.
        """
        ...


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
            return cls2.from_data(
                plugin_path,
                plugin_data,
                os.path.dirname(plugin_path) == first_party_plugin_directory(),
            )

    @classmethod
    @abstractmethod
    def from_data(
        cls, plugin_path: str, plugin_data: dict, first_party: bool
    ) -> PluginContainer:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        if cls.FormatVersion in _plugin_classes:
            raise ValueError(
                f"Two classes have been registered with format version {cls.FormatVersion}"
            )
        _plugin_classes[cls.FormatVersion] = cls


class PluginContainerV1(PluginContainer):
    FormatVersion = 1

    @classmethod
    def from_data(
        cls, plugin_path: str, plugin_data: dict, first_party: bool
    ) -> PluginContainerV1:
        """
        Populate a PluginContainer instance from the data in a directory.
        plugin_path is the system path to a directory containing a plugin.json file.
        """
        # Get the plugin identifier
        plugin_identifier = plugin_data.get("identifier")
        if not isinstance(plugin_identifier, str):
            raise TypeError("plugin.json[identifier] must be a string")
        if not plugin_identifier.isidentifier():
            raise ValueError(
                "plugin.json[identifier] must be a valid python identifier"
            )

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
        if not isinstance(depends, list) and all(isinstance(d, str) for d in depends):
            raise TypeError(
                'plugin.json[depends] must be a list of string identifiers and version specifiers if defined.\nEg. ["plugin_1 ~=1.0", "plugin_2 ~=1.3"]'
            )

        # Get the locked state
        locked = bool(first_party and plugin_data.get("locked"))

        parsed_depends = tuple(map(PluginRequirement.from_string, depends))

        return cls(
            PluginData(
                PluginUID(plugin_identifier, plugin_version),
                plugin_path,
                plugin_name,
                parsed_depends,
                locked,
            )
        )
