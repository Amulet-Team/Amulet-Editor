from __future__ import annotations
import os
from typing import Optional
from contextlib import suppress

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

import amulet_team_3d_viewer
from ._view_3d import View3D


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[ATranslator] = None

View3DID = "68817e4c-32e3-43f8-ac61-9d7352c6329d"
view_3d_button: ButtonProxy | None = None


def load_plugin() -> None:
    global _translator, view_3d_button
    if get_level() is not None:
        _translator = ATranslator()
        _locale_changed()
        QCoreApplication.installTranslator(_translator)
        amulet_team_locale.locale_changed.connect(_locale_changed)

        register_widget(View3D)

        register_layout(
            View3DID,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(View3D.__qualname__),)),
                ),
                (),
            ),
        )

        # Set up the 3D View button
        view_3d_button = create_layout_button(View3DID)
        view_3d_button.set_icon(tablericons.three_d_cube_sphere)
        view_3d_button.set_name("3D Editor")


def _locale_changed() -> None:
    assert _translator is not None
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_3d_viewer.__path__, "_resources", "lang"),
    )


def unload_plugin() -> None:
    if view_3d_button is not None:
        view_3d_button.delete()
        unregister_layout(View3DID)
    with suppress(ValueError):
        unregister_widget(View3D)
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
