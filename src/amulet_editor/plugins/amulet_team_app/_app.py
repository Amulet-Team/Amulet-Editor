from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QGuiApplication

from amulet_editor import __version__
from amulet_editor.data import build
from amulet_editor.application import appearance
from amulet_editor.application.appearance import Theme

from ._windows._amulet_main_window import AmuletMainWindow


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

        # Apply theme
        appearance.changed.connect(self.apply_theme)
        self.apply_theme(appearance.theme())

        self._main_window = AmuletMainWindow()
        self._main_window.showMaximized()

    def apply_theme(self, theme: Theme) -> None:
        theme.apply(self)
