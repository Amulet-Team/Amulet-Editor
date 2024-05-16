from __future__ import annotations

import json
import os.path
from typing import Optional, Type, Protocol, Any, TypeVar
from abc import ABC, abstractmethod
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from amulet_editor.data.paths._plugin import first_party_plugin_directory
from ._plugin import PluginV1
from ._data import PluginData, PluginDataDepends
from ._state import PluginState
from ._requirement import Requirement
from ._uid import LibraryUID


_plugin_classes: dict[int, Type[PluginContainer]] = {}


T = TypeVar("T")


def dynamic_cast(obj: Any, cls: type[T], msg: str = "") -> T:
    if isinstance(obj, cls):
        return obj
    if msg:
        raise TypeError(msg)
    else:
        raise TypeError(f"Cast to type {cls} failed.")


class Plugin(Protocol):
    def load_plugin(self) -> None:
        """
        Logic run when the plugin is started.
        All dependencies will be started when this is called.
        Plugins may implement this method but must not call it.
        """
        ...

    def unload_plugin(self) -> None:
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
    plugin: Optional[PluginV1]
    state: PluginState

    FormatVersion: int = -1

    def __init__(self, data: PluginData):
        self.data = data
        self.instance = None
        self.plugin = None
        self.state = PluginState.Disabled

    @classmethod
    def from_path(cls, plugin_path: str) -> PluginContainer:
        """
        Populate a PluginContainer instance from the data in a directory.
        plugin_path is the system path to a directory containing a plugin.json file.
        """
        with open(os.path.join(plugin_path, "plugin.json")) as f:
            plugin_data = dynamic_cast(json.load(f), dict, "plugin.json must be a dictionary.")

        # Get the plugin identifier
        format_version = dynamic_cast(plugin_data.get("format_version", 1), int, "plugin.json[format_version] must be an int")
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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if cls.FormatVersion == -1:
            raise NotImplementedError("FormatVersion has not been set.")
        if cls.FormatVersion in _plugin_classes:
            raise ValueError(
                f"Two classes have been registered with format version {cls.FormatVersion}"
            )
        _plugin_classes[cls.FormatVersion] = cls


class PluginContainerV1(PluginContainer):
    FormatVersion = 1

    def __repr__(self) -> str:
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
        plugin_identifier = dynamic_cast(plugin_data.get("identifier"), str, "plugin.json[identifier] must be a string")
        if not plugin_identifier.isidentifier():
            raise ValueError(
                "plugin.json[identifier] must be a valid python identifier"
            )

        # Get the plugin version
        plugin_version_string = dynamic_cast(plugin_data.get("version"), str, "plugin.json[version] must be a PEP 440 version string")
        plugin_version = Version(plugin_version_string)

        # Get the plugin name
        plugin_name = dynamic_cast(plugin_data.get("name"), str, "plugin.json[name] must be a string")

        # Get the plugin dependencies
        depends_raw = dynamic_cast(plugin_data.get("depends"), dict, 'plugin.json[depends] must be a dictionary of the form {"python": "~=3.9", "library": [], "plugin": []}')

        python_raw = dynamic_cast(depends_raw.get("python"), str, 'plugin.json[depends][python] must be a string of the form "~=3.9"')
        python = SpecifierSet(python_raw)

        library_depends_raw = dynamic_cast(depends_raw.get("library", []), list, "plugin.json[depends][library] must be a list")
        if not all(isinstance(d, str) for d in library_depends_raw):
            raise TypeError(
                'plugin.json[depends][library] must be a list of string identifiers and version specifiers if defined.\nEg. ["PySide6_Essentials~=6.4"]'
            )
        library_depends = tuple(map(Requirement.from_string, library_depends_raw))

        plugin_depends_raw = dynamic_cast(depends_raw.get("plugin", []), list, "plugin.json[depends][plugin] must be a list")
        if not all(isinstance(d, str) for d in plugin_depends_raw):
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
