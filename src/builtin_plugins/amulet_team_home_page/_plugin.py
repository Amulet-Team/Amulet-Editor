from __future__ import annotations
import os

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.data.level import get_level
from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import tablericons
import amulet_team_locale
from amulet_team_main_window import (
    register_widget,
    unregister_widget,
    register_layout,
    unregister_layout,
    WidgetConfig,
    WidgetStackConfig,
    WindowConfig,
    LayoutConfig,
    ButtonProxy,
    create_layout_button,
)

import amulet_team_home_page
from .home import HomeWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: ATranslator | None = None

HomeLayoutID = "073bfd20-249e-4e0c-ad41-0bcb0c9db89f"
home_button: ButtonProxy | None = None


def load_plugin() -> None:
    global _translator, home_button
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    register_widget(HomeWidget)

    register_layout(
        HomeLayoutID,
        LayoutConfig(
            WindowConfig(
                None, None, WidgetStackConfig((WidgetConfig(HomeWidget.__qualname__),))
            ),
            (),
        ),
    )

    # Set up the home button
    home_button = create_layout_button(HomeLayoutID)
    home_button.set_icon(tablericons.home)
    home_button.set_name("Home")

    if get_level() is None:
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
    if home_button is not None:
        home_button.delete()
        unregister_layout(HomeLayoutID)

    unregister_widget(HomeWidget)
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
