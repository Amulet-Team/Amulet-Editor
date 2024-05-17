from __future__ import annotations
import os
from typing import Optional

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.data.level import get_level
from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

import amulet_team_locale
import amulet_team_main_window
import tablericons

import amulet_team_3d_viewer
from ._view_3d import View3D


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None
view_3d_button: Optional[amulet_team_main_window.ButtonProxy] = None


def _set_view_3d_layout():
    amulet_team_main_window.get_main_window().set_layout(View3D)


def load_plugin():
    global _translator, view_3d_button
    if get_level() is not None:
        _translator = ATranslator()
        _locale_changed()
        QCoreApplication.installTranslator(_translator)
        amulet_team_locale.locale_changed.connect(_locale_changed)
        amulet_team_main_window.register_widget(View3D)

        view_3d_button = amulet_team_main_window.add_toolbar_button(sticky=True)
        view_3d_button.set_icon(tablericons.three_d_cube_sphere)
        view_3d_button.set_name("3D Editor")
        view_3d_button.set_callback(_set_view_3d_layout)


def _locale_changed():
    assert _translator is not None
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_3d_viewer.__path__, "_resources", "lang"),
    )


def unload_plugin():
    QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
