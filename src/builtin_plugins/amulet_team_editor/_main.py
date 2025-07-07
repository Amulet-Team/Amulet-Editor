from __future__ import annotations

from argparse import ArgumentParser
import logging
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QLocale

from amulet.level import get_level
from amulet.level.loader import LevelLoaderPathToken

from amulet.app import __version__
from amulet.app.cli import FullArgs, Command
from amulet.app.resource import get_resource_path
from amulet.app.exception import CatchExceptionDialog
from amulet.app.localisation import Translator, locale_changed

import tablericons
import amulet_team_level

import amulet_team_editor
from amulet_team_editor.window._main import (
    get_main_window,
    destroy_main_window,
    ButtonProxy,
)
from amulet_team_editor.widget._home import HomeWidget
from amulet_team_editor.widget._level_info import LevelInfoWidget
from amulet_team_editor.widget import register_widget, unregister_widget
from amulet_team_editor.layout import (
    register_layout,
    unregister_layout,
    LayoutConfig,
    WindowConfig,
    WidgetStackConfig,
    WidgetConfig,
    create_layout_button,
)
from amulet_team_editor._signal import init_editor, destroy_editor

log = logging.getLogger(__name__)


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Translator | None = None

HomeLayoutID = "073bfd20-249e-4e0c-ad41-0bcb0c9db89f"
home_button: ButtonProxy | None = None

LevelInfoLayoutID = "4de0ebcd-f789-440f-9526-e6cc5d77caff"
level_info_button: ButtonProxy | None = None


def _init_app() -> None:
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        raise RuntimeError("No QApplication instance")
    app.setApplicationName("Amulet Editor")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(get_resource_path("icons/amulet/Icon.ico")))


def _load_translations() -> None:
    if _translator is None:
        return
    _translator.load_lang(
        QLocale(),
        "",
        directory=os.path.join(*amulet_team_editor.__path__, "_resources", "lang"),
    )


def _init_editor() -> None:
    global home_button, level_info_button

    register_widget(HomeWidget)
    register_widget(LevelInfoWidget)

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

    if amulet_team_level.get_level() is None:
        # Make the home layout active by clicking the button
        home_button.click()
    else:
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


def _destroy_editor() -> None:
    if home_button is not None:
        home_button.delete()
        unregister_layout(HomeLayoutID)

    if level_info_button is not None:
        level_info_button.delete()
        unregister_layout(LevelInfoLayoutID)

    unregister_widget(HomeWidget)
    unregister_widget(LevelInfoWidget)


def _main(args: FullArgs) -> None:
    global _translator

    # Initialise the application
    _init_app()

    # Load the level
    if args.command is None:
        amulet_team_level.set_level(None)
    else:
        log.debug("Loading level.")
        level_path = args.level_path
        with CatchExceptionDialog(f"Failed loading level at path {level_path}", suppress=False):
            level = get_level(
                LevelLoaderPathToken(level_path)
            )  # TODO: make this generic
            level.open()
            amulet_team_level.set_level(level)

    # Load the translations
    _translator = Translator()
    _load_translations()
    QApplication.installTranslator(_translator)
    locale_changed.connect(_load_translations)

    # Register widgets and layouts
    _init_editor()
    destroy_editor.connect(_destroy_editor)
    init_editor.emit()

    # Show the window
    get_main_window().showMaximized()


def unload() -> None:
    global _translator

    if _translator is not None:
        QApplication.removeTranslator(_translator)
        _translator = None

    destroy_main_window()


def _init_argparse(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--level_path",
        type=str,
        help="The Minecraft world or structure to open. Default opens no level",
        action="store",
        dest="level_path",
        default=None,
    )


_editor_command: Command | None = None


def get_command() -> Command:
    global _editor_command
    if _editor_command is None:
        _editor_command = Command(
            name="editor",
            main_func=_main,
            init_argparse=_init_argparse,
        )
    return _editor_command
