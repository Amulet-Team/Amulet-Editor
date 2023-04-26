from __future__ import annotations
from typing import Optional
import sys
import os
import logging
from datetime import datetime

from PySide6.QtCore import Qt, Slot, QLocale, QCoreApplication, QTimer
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
from amulet_editor.data.paths import logging_directory

from . import appearance
from ._cli import parse_args, BROKER

log = logging.getLogger(__name__)


class AmuletApp(QApplication):
    def __init__(self):
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(build.get_resource("icons/amulet/Icon.ico")))
        self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        self._translator = ATranslator()
        self._locale_changed()
        QCoreApplication.installTranslator(self._translator)
        locale_changed.connect(self._locale_changed)

        appearance.theme().apply(self)

        self.lastWindowClosed.connect(self._last_window_closed)
        QTimer.singleShot(0, plugin_manager.load)

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
    args = parse_args()

    logging.basicConfig(level=args.logging_level, format=args.logging_format, force=True)

    file_path = os.path.join(logging_directory(), f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt")
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(logging.Formatter(args.logging_format))
    logging.getLogger().addHandler(file_handler)

    is_broker = args.level_path == BROKER
    messaging.init_rpc(is_broker)

    if is_broker:
        # Dummy application to get a main loop.
        app = QApplication()
    else:
        app = AmuletApp()
        # The broker cannot have a level
        level_path: Optional[str] = args.level_path
        if level_path is None:
            _level.level = None
        else:
            log.debug("Loading level.")
            with DisplayException(f"Failed loading level at path {level_path}"):
                _level.level = amulet.load_level(level_path)

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
