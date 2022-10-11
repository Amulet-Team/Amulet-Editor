import os
import subprocess
import sys

from amulet_editor.data import packages, build
from amulet_editor.data.build import PUBLIC_DATA
from amulet_editor.application import appearance
from amulet_editor.application.appearance import Theme
from amulet_editor.application.windows._amulet_window import AmuletWindow
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


class AmuletEditor(QApplication):
    def __init__(self) -> None:
        super().__init__()
        self.setApplicationName(PUBLIC_DATA["app_name"])
        self.setApplicationVersion(PUBLIC_DATA["version"])
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

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
        theme.apply(self)

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
