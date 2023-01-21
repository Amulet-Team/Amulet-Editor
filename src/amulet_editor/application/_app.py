from __future__ import annotations
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from amulet_editor import __version__
from amulet_editor.data import build
import amulet_editor.data.plugin._manager as plugin_manager
from . import appearance


class AmuletApp(QApplication):
    def __init__(self):
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        appearance.theme().apply(self)

        self.lastWindowClosed.connect(plugin_manager.unload)
        plugin_manager.load()

    @staticmethod
    def instance() -> Optional[AmuletApp]:
        return QApplication.instance()


def main():
    sys.exit(AmuletApp().exec())
