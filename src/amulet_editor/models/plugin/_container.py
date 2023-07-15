from __future__ import annotations

import json
import os.path
from typing import Optional, Type, Protocol
from abc import ABC, abstractmethod
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from amulet_editor.data.paths._plugin import first_party_plugin_directory
from ._data import PluginData, PluginDataDepends
from ._state import PluginState
from ._requirement import Requirement
from ._uid import LibraryUID


_plugin_classes: dict[int, Type[PluginContainer]] = {}


class Plugin(Protocol):
    def load_plugin(self):
        """
        Logic run when the plugin is started.
        All dependencies will be started when this is called.
        Plugins may implement this method but must not call it.
        """
        ...

    def unload_plugin(self):
        """
        Logic run when the plugin is stopped.
        Dependents will be stopped at this point but dependencies are not.
        This must leave the program in the same state as it was before load_plugin was called.
        Plugins may implement this method but must not call it.
        """
        ...


class PluginContainer(ABC):
    data: PluginData
    instance: Optional[Plugin]  # The instance of the plugin.
    state: PluginState

    FormatVersion: int = None

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
        if cls.FormatVersion is None:
            raise NotImplementedError("FormatVersion has not been set.")
        if cls.FormatVersion in _plugin_classes:
            raise ValueError(
                f"Two classes have been registered with format version {cls.FormatVersion}"
            )
        _plugin_classes[cls.FormatVersion] = cls


class PluginContainerV1(PluginContainer):
    FormatVersion = 1

    def __repr__(self):
        return f"PluginContainerV1({self.data.path})"

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
        depends_raw: dict = plugin_data.get("depends")
        if not isinstance(depends_raw, dict):
            raise TypeError(
                'plugin.json[depends] must be a dictionary of the form {"python": "~=3.9", "library": [], "plugin": []}'
            )

        python_raw = depends_raw.get("python")
        if not isinstance(python_raw, str):
            raise TypeError(
                'plugin.json[depends][python] must be a string of the form "~=3.9"'
            )
        python = SpecifierSet(python_raw)

        library_depends_raw: dict = depends_raw.get("library", [])
        if not isinstance(library_depends_raw, list) and all(
            isinstance(d, str) for d in library_depends_raw
        ):
            raise TypeError(
                'plugin.json[depends][library] must be a list of string identifiers and version specifiers if defined.\nEg. ["PySide6_Essentials~=6.4"]'
            )
        library_depends = tuple(map(Requirement.from_string, library_depends_raw))

        plugin_depends_raw: dict = depends_raw.get("plugin", [])
        if not isinstance(plugin_depends_raw, list) and all(
            isinstance(d, str) for d in plugin_depends_raw
        ):
            raise TypeError(
                'plugin.json[depends][plugin] must be a list of string identifiers and version specifiers if defined.\nEg. ["plugin_1~=1.0", "plugin_2~=1.3"]'
            )
        plugin_depends = tuple(map(Requirement.from_string, plugin_depends_raw))

        # Get the locked state
        locked = bool(first_party and plugin_data.get("locked"))

        return cls(
            PluginData(
                LibraryUID(plugin_identifier, plugin_version),
                plugin_path,
                plugin_name,
                PluginDataDepends(
                    python,
                    library_depends,
                    plugin_depends,
                ),
                locked,
            )
        )
