from __future__ import annotations

from amulet.app.plugin import PluginV1
from amulet_editor.application.command import register_command, unregister_command

from ._main import get_command, unload


def load_plugin() -> None:
    register_command(get_command())


def unload_plugin() -> None:
    unload()
    unregister_command(get_command())


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
