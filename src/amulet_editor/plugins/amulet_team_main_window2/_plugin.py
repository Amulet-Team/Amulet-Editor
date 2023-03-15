from __future__ import annotations
from typing import Optional

from .application.windows.main_window import AmuletMainWindow


window: Optional[AmuletMainWindow] = None


def load_plugin():
    global window
    window = AmuletMainWindow()
    window.showMaximized()
