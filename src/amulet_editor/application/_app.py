from __future__ import annotations

from typing import Optional
import os

from PySide6.QtCore import Slot, QLocale, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

import amulet_editor
from amulet_editor import __version__
from amulet_editor.models.localisation import ATranslator
from amulet.app.resource import get_resource_path
from amulet_editor.data._localisation import locale_changed
import amulet.app.plugin._manager as plugin_manager

from . import appearance

# class AmuletApp(QApplication):
#     def __init__(self) -> None:
#         super().__init__()
#
#
#         appearance.theme().apply(self)
