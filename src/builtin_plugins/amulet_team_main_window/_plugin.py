from __future__ import annotations

from ._application.windows.main_window import AmuletMainWindow
from amulet_editor.models.plugin import PluginV1


def load_plugin() -> None:
    AmuletMainWindow.instance().showMaximized()


plugin = PluginV1(load=load_plugin)
