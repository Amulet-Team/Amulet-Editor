from __future__ import annotations

from amulet_team_main_window.application.windows.main_window import AmuletMainWindow
from amulet_editor.models.plugin import PluginV1


window: AmuletMainWindow | None = None


def load_plugin() -> None:
    global window
    window = AmuletMainWindow()
    window.showMaximized()


plugin = PluginV1(load=load_plugin)
