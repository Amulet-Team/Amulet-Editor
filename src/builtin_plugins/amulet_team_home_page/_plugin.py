from __future__ import annotations
import os

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import amulet_team_locale
import amulet_team_main_window
from amulet_team_main_window import register_widget

import amulet_team_home_page
from .home import HomeWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: ATranslator | None = None


def load_plugin() -> None:
    global _translator
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    register_widget(HomeWidget)


def _locale_changed() -> None:
    assert _translator is not None
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_home_page.__path__, "resources", "lang"),
    )


def unload_plugin() -> None:
    amulet_team_main_window.unregister_widget(HomeWidget)
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
