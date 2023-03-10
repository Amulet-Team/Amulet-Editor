from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING
from packaging.specifiers import SpecifierSet

if TYPE_CHECKING:
    from ._uid import LibraryUID
    from ._requirement import Requirement


class PluginDataDepends(NamedTuple):
    """Static, publicly accessible data about a plugin's dependencies"""

    python: SpecifierSet
    library: tuple[Requirement, ...]
    plugin: tuple[
        Requirement, ...
    ]  # The plugins that this plugin depends on. This plugin will only be loaded once these plugins have been loaded.


class PluginData(NamedTuple):
    """Static, publicly accessible data about a plugin"""

    uid: LibraryUID  # The unique identifier for the plugin. Made up of the plugin id and the version number. No two plugins may have the same UID.
    path: str  # The root path of the plugin.
    name: str  # The public name of the plugin.
    depends: PluginDataDepends  # The dependencies for the plugin
    locked: bool  # Is the plugin locked on. Only accessible to first party plugins.
