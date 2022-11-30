from amulet_editor import __version__
from amulet_editor.data import packages, build
from amulet_editor.application import appearance
from amulet_editor.application.appearance import Theme
from amulet_editor.application.windows._amulet_window import AmuletWindow
from amulet_editor.application.windows._amulet_landing_window import AmuletLandingWindow
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


class AmuletEditorBaseApp(QApplication):
    def __init__(self) -> None:
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # Load builtin packages
        packages.install_builtins()

        # Apply theme
        appearance.changed.connect(self.apply_theme)
        self.apply_theme(appearance.theme())

    def apply_theme(self, theme: Theme) -> None:
        theme.apply(self)


class AmuletEditorStartupApp(AmuletEditorBaseApp):
    def __init__(self):
        super().__init__()
        self._main_window = AmuletLandingWindow()
        self._main_window.showMaximized()


class AmuletEditorLevelApp(AmuletEditorBaseApp):
    def __init__(self):
        super().__init__()
        self._main_window = AmuletWindow()
        self._main_window.showMaximized()
