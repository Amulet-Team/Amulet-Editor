from __future__ import annotations
import os
from typing import Optional

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator

import amulet_team_locale

import amulet_team_3d_viewer


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None


def load_plugin():
    global _translator
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)


def _locale_changed():
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_3d_viewer.__path__, "_resources", "lang"),
    )


def unload_plugin():
    QCoreApplication.removeTranslator(_translator)
