from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ._uid import PluginUID
    from ._requirement import PluginRequirement


class PluginData(NamedTuple):
    """Static, publicly accessible data about a plugin"""
    uid: PluginUID  # The unique identifier for the plugin. Made up of the plugin id and the version number. No two plugins may have the same UID.
    path: str  # The root path of the plugin.
    name: str  # The public name of the plugin.
    depends: tuple[PluginRequirement, ...]  # The plugins that this plugin depends on. This plugin will only be loaded once these plugins have been loaded.
    locked: bool  # Is the plugin locked on. Only accessible to first party plugins.
