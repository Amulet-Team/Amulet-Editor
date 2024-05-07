from __future__ import annotations
import os

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import amulet_team_locale
import amulet_team_main_window
import tablericons

import amulet_team_home_page
from .home import HomeWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: ATranslator | None = None

home_button: amulet_team_main_window.ButtonProxy | None = None


def _set_home_layout() -> None:
    amulet_team_main_window.get_main_window().set_layout(HomeWidget)


def load_plugin() -> None:
    global _translator, home_button
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    amulet_team_main_window.register_widget(HomeWidget)

    # Set up the button
    home_button = amulet_team_main_window.add_toolbar_button(sticky=True)
    home_button.set_icon(tablericons.home)
    home_button.set_name("Home")
    home_button.set_callback(_set_home_layout)

    # Make the home layout active by clicking the button
    home_button.click()


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


plugin = PluginV1(load_plugin, unload_plugin)
