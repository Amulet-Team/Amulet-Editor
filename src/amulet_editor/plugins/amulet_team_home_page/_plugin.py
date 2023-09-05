from __future__ import annotations
import os
from typing import Optional

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import amulet_team_locale
import amulet_team_main_window2

import amulet_team_home_page
from .home import HomeWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None


def _set_home_layout(proxy):
    proxy.set_layout(HomeWidget)


def load_plugin():
    global _translator
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    amulet_team_main_window2.register_widget(HomeWidget)
    amulet_team_main_window2.add_toolbar_button(
        "amulet_team:home", "home.svg", "Home", _set_home_layout
    )
    amulet_team_main_window2.get_main_window().set_layout(HomeWidget)


def _locale_changed():
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_home_page.__path__, "resources", "lang"),
    )


def unload_plugin():
    amulet_team_main_window2.unregister_widget(HomeWidget)
    QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load_plugin, unload_plugin)
