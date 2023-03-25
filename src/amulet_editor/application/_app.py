from __future__ import annotations
from typing import Optional
import sys
import os
import argparse
import logging

from PySide6.QtCore import Qt, Slot, QLocale, QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

import amulet
import amulet_editor
from amulet_editor import __version__
from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.widgets import DisplayException
from amulet_editor.data import build
from amulet_editor.data._localisation import locale_changed
import amulet_editor.data.plugin._manager as plugin_manager
from amulet_editor.data.project import _level
import amulet_editor.data.process._messaging3 as messaging

from . import appearance


class AmuletApp(QApplication):
    def __init__(self):
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self._translator = ATranslator()
        self._locale_changed()
        QCoreApplication.installTranslator(self._translator)
        locale_changed.connect(self._locale_changed)

        appearance.theme().apply(self)

        self.lastWindowClosed.connect(self._last_window_closed)
        plugin_manager.load()

    @staticmethod
    def instance() -> Optional[AmuletApp]:
        return QApplication.instance()

    @Slot()
    def _last_window_closed(self):
        # The unload method opens a window and then closes it.
        # We must unbind this signal so that it does not end in a loop.
        self.lastWindowClosed.disconnect(self._last_window_closed)
        # unload all the plugins
        plugin_manager.unload()
        # Forcefully quit the application just in case a plugin opened a window during unload.
        self.quit()

    @Slot()
    def _locale_changed(self):
        self._translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(*amulet_editor.__path__, "resources", "lang"),
        )


def app_main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--level_path",
        type=str,
        help="The Minecraft world or structure to open. Default opens no level",
        action="store",
        dest="level_path",
        default=None
    )

    parser.add_argument(
        "--logging_level",
        type=int,
        help="The logging level to set. CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10. Default is WARNING",
        action="store",
        dest="logging_level",
        default=logging.WARNING
    )

    parser.add_argument(
        "--broker",
        help=argparse.SUPPRESS,
        action="store_true",
        dest="broker",
    )

    args, _ = parser.parse_known_args()

    logging.basicConfig(level=args.logging_level, format="%(levelname)s - %(message)s")
    logging.getLogger().setLevel(args.logging_level)

    messaging.init_state(args.broker)
    if args.broker:
        app = QApplication()

    else:
        # The broker cannot have a level
        level_path: Optional[str] = args.level_path
        if level_path is None:
            _level.level = None
        else:
            with DisplayException(f"Failed loading level at path {level_path}"):
                _level.level = amulet.load_level(level_path)

        app = AmuletApp()

    sys.exit(app.exec())
