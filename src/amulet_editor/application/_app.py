from __future__ import annotations

from typing import Optional
import os

from PySide6.QtCore import Slot, QLocale, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

import amulet_editor
from amulet_editor import __version__
from amulet_editor.models.localisation import ATranslator
from amulet_editor.resources import get_resource
from amulet_editor.data._localisation import locale_changed
import amulet_editor.data.plugin._manager as plugin_manager

from . import appearance


class AmuletApp(QApplication):
    def __init__(self) -> None:
        super().__init__()
        self.setApplicationName("Amulet Editor")
        self.setApplicationVersion(__version__)
        self.setWindowIcon(QIcon(get_resource("icons/amulet/Icon.ico")))

        self._translator = ATranslator()
        self._locale_changed()
        QCoreApplication.installTranslator(self._translator)
        locale_changed.connect(self._locale_changed)

        appearance.theme().apply(self)

        self.lastWindowClosed.connect(self._last_window_closed)
        QTimer.singleShot(0, plugin_manager.load)

    @staticmethod
    def instance() -> Optional[AmuletApp]:
        instance = QApplication.instance()
        assert isinstance(instance, AmuletApp)
        return instance

    @Slot()
    def _last_window_closed(self) -> None:
        # The unload method opens a window and then closes it.
        # We must unbind this signal so that it does not end in a loop.
        self.lastWindowClosed.disconnect(self._last_window_closed)
        # unload all the plugins
        plugin_manager.unload()
        # Forcefully quit the application just in case a plugin opened a window during unload.
        self.quit()

    @Slot()
    def _locale_changed(self) -> None:
        self._translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(*amulet_editor.__path__, "resources", "lang"),
        )
