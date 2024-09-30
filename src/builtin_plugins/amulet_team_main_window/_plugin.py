from __future__ import annotations

from ._main_window import get_main_window, destroy_main_window
from amulet_editor.models.plugin import PluginV1


def load_plugin() -> None:
    get_main_window().showMaximized()


def unload_plugin() -> None:
    destroy_main_window()


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
