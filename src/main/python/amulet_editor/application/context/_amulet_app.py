import os
import subprocess
import sys

from amulet_editor.application import appearance
from amulet_editor.application.appearance import Theme
from amulet_editor.application.windows._amulet_window import AmuletWindow
from amulet_editor.data import packages
from amulet_editor.data.build import PUBLIC_DATA
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


class AmuletEditor:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._app.setApplicationName(PUBLIC_DATA["app_name"])

        # Load builtin packages
        packages.install_builtins()

        # Create window
        self.main_window = AmuletWindow()
        self.main_window.act_new_window.triggered.connect(self.new_instance)

        # Apply theme after generating components
        appearance.changed.connect(self.apply_theme)
        self.apply_theme(appearance.theme())

        # Show window
        self.main_window.showMaximized()

    def apply_theme(self, theme: Theme) -> None:
        theme.apply(self.app)

    def new_instance(self):
        import amulet_editor

        subprocess.Popen(
            [
                sys.executable,
                os.path.join(
                    os.path.dirname(amulet_editor.__file__),
                    os.path.basename(PUBLIC_DATA["main_module"]),
                ),
            ]
        )

    @property
    def app(self) -> QApplication:
        return self._app
