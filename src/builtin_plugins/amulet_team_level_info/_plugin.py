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
import amulet_team_level_info
from .level_info import LevelInfoWidget


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: ATranslator | None = None

LevelInfoLayoutID = "4de0ebcd-f789-440f-9526-e6cc5d77caff"
level_info_button: ButtonProxy | None = None


def load_plugin() -> None:
    global _translator, level_info_button
    _translator = ATranslator()
    _locale_changed()
    QCoreApplication.installTranslator(_translator)
    amulet_team_locale.locale_changed.connect(_locale_changed)

    register_widget(LevelInfoWidget)

    if get_level() is not None:
        register_layout(
            LevelInfoLayoutID,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(LevelInfoWidget.__qualname__),)),
                ),
                (),
            ),
        )

        # Set up the home button
        level_info_button = create_layout_button(LevelInfoLayoutID)
        level_info_button.set_icon(tablericons.file_info)
        level_info_button.set_name("Level Info")
        level_info_button.click()


def _locale_changed() -> None:
    assert _translator is not None
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_level_info.__path__, "resources", "lang"),
    )


def unload_plugin() -> None:
    if level_info_button is not None:
        level_info_button.delete()
        unregister_layout(LevelInfoLayoutID)
    unregister_widget(LevelInfoWidget)
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
