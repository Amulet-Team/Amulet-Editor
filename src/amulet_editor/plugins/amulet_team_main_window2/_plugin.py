from __future__ import annotations
from typing import Optional

from amulet_team_main_window2.application.windows.main_window import AmuletMainWindow
from amulet_editor.models.plugin import PluginV1


window: Optional[AmuletMainWindow] = None


def load_plugin():
    global window
    window = AmuletMainWindow()
    window.showMaximized()


plugin = PluginV1(load_plugin)
