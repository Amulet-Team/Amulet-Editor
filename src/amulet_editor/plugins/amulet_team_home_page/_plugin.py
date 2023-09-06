from __future__ import annotations
import os
from typing import Optional

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import amulet_team_locale
import amulet_team_main_window2
import tablericons

import amulet_team_home_page
from .home import HomeWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None

home_button: Optional[amulet_team_main_window2.ButtonProxy] = None


def _set_home_layout():
    amulet_team_main_window2.get_main_window().set_layout(HomeWidget)


def load_plugin():
    global _translator, home_button
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    amulet_team_main_window2.register_widget(HomeWidget)

    # Set up the button
    home_button = amulet_team_main_window2.add_toolbar_button(sticky=True)
    home_button.set_icon(tablericons.home)
    home_button.set_name("Home")
    home_button.set_callback(_set_home_layout)

    # Make the home layout active by clicking the button
    home_button.click()


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
