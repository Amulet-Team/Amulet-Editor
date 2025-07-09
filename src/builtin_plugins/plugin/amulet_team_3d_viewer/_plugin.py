from __future__ import annotations
import os
from typing import Optional
from contextlib import suppress

from PySide6.QtCore import QLocale, QCoreApplication

from amulet.app.localisation import Translator, locale_changed
from amulet.app.plugin import PluginV1

from plugin import tablericons
from plugin.amulet_team_level import get_level
from plugin.amulet_team_editor import (
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
    init_editor,
    destroy_editor,
)

from plugin import amulet_team_3d_viewer
from ._view_3d import View3D


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Optional[Translator] = None

View3DID = "68817e4c-32e3-43f8-ac61-9d7352c6329d"
view_3d_button: ButtonProxy | None = None


def _load_translations() -> None:
    if _translator is None:
        return
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_3d_viewer.__path__, "_resources", "lang"),
    )


def _init_editor() -> None:
    global _translator, view_3d_button
    if get_level() is not None:
        _translator = Translator()
        _load_translations()
        QCoreApplication.installTranslator(_translator)
        locale_changed.connect(_load_translations)

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


def _destroy_editor() -> None:
    if view_3d_button is not None:
        view_3d_button.delete()
        unregister_layout(View3DID)
    with suppress(ValueError):
        unregister_widget(View3D)
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


def load_plugin() -> None:
    init_editor.connect(_init_editor)
    destroy_editor.connect(_destroy_editor)


def unload_plugin() -> None:
    init_editor.disconnect(_init_editor)
    destroy_editor.disconnect(_destroy_editor)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
