from __future__ import annotations
from typing import TYPE_CHECKING
from weakref import proxy

from runtime_final import final

if TYPE_CHECKING:
    from ._plugin import Plugin


class PluginAPI:
    """
    This is the publicly facing API that your plugin exposes.
    Any plugin can access any public functions or attributes that you store in this class.
    """

    @final
    def __init__(self, plugin: Plugin):
        # This plugin may use the _plugin attribute to access the plugin instance but other plugins must not.
        self._plugin = proxy(plugin)
        self._on_init()

    def _on_init(self):
        """
        Initialise any desired attributes.
        Third party plugins may overwrite this method.
        """
        pass
