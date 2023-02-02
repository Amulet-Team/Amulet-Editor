from __future__ import annotations
import os
from typing import Optional

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator

import amulet_team_locale


from amulet_team_main_window.api import (
    register_view,
    unregister_view,
    get_active_window,
)

import amulet_team_home_page
from .home import HomeView


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None


def load_plugin():
    global _translator
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    register_view(HomeView, "home.svg", "Home")
    get_active_window().activate_view(HomeView)


def _locale_changed():
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_home_page.__path__, "resources", "lang"),
    )


def unload_plugin():
    unregister_view(HomeView)
    QCoreApplication.removeTranslator(_translator)
