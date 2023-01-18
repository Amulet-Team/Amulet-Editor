import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QGuiApplication

from amulet_editor import __version__
from amulet_editor.data import build
import amulet_editor.data.plugin._manager as plugin_manager


def hide_instance():
    raise RuntimeError("You cannot access the app instance.")


QGuiApplication.instance = hide_instance


class AmuletApp(QApplication):
    def __init__(self) -> None:
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        plugin_manager.init()


app: Optional[AmuletApp] = None


def main():
    global app
    app = AmuletApp()
    sys.exit(app.exec())
