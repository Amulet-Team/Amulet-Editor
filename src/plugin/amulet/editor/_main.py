from __future__ import annotations

from typing import NoReturn
from argparse import ArgumentParser, Namespace
import logging
import os
import sys
import traceback

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QSurfaceFormat
from PySide6.QtCore import QLocale, Qt, QCoreApplication, QThreadPool

from amulet.level import get_level
from amulet.level.loader import LevelLoaderPathToken

from amulet.app import __version__
from amulet.app.resource import get_resource_path
from amulet.app.exception import display_exception, CatchExceptionDialog
from amulet.app.localisation import Translator, locale_changed
from amulet.app.app import AmuletApp
from amulet.app.style import set_style
from amulet.app.invoke import invoke

from . import __path__ as editor_plugin_path
from ._main_window import init_and_show_editor, get_amulet_editor
from ._init import init_editor_tools

log = logging.getLogger(__name__)


class EditorNamespace(Namespace):
    level_paths: list[str]


def _load_levels(level_paths: list[str]) -> None:
    with CatchExceptionDialog("Error loading levels", logger=log):
        # Load the level(s)
        is_first = True
        for level_path in level_paths:
            log.debug(f'Loading level "{level_path}".')
            try:
                level = get_level(
                    LevelLoaderPathToken(level_path)
                )  # TODO: make this generic
                level.open()
            except Exception as e:
                log.exception(e)
                display_exception(
                    title=f"Failed loading level at path {level_path}",
                    error=str(e),
                    traceback="".join(traceback.format_exc()),
                )
            else:
                # TODO: This will crash if the window is closed
                invoke(lambda: get_amulet_editor().add_level_tab(level, show=is_first))
                is_first = False


def main(argv: list[str]) -> NoReturn:
    parser = ArgumentParser("amulet_editor amulet_editor")
    parser.add_argument(
        "level_paths",
        type=str,
        nargs="*",
        help="The Minecraft worlds or structures to open",
        action="store",
    )
    args = parser.parse_args(argv, namespace=EditorNamespace())

    # TODO: check if a session is already running and open the levels in that session

    # Check an app has not already been created
    if QApplication.instance() is not None:
        raise RuntimeError("QApplication has already been initialized")

    # Allow context sharing between widgets that do not share the same top level window.
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Set the default surface format. Apparently this is required for some platforms.
    surface_format = QSurfaceFormat()
    surface_format.setDepthBufferSize(24)
    surface_format.setVersion(3, 2)
    surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(surface_format)

    # Initialise the application
    app = AmuletApp()
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(get_resource_path("icons/amulet/Icon.ico")))

    set_style("amulet")

    # Load the translations
    translator = Translator()

    def _load_translations() -> None:
        translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(editor_plugin_path[0], "_resources", "lang"),
        )

    _load_translations()
    QApplication.installTranslator(translator)
    locale_changed.connect(_load_translations)

    app.setApplicationName(QApplication.translate("plugin.amulet.editor", "app_name"))

    init_and_show_editor()
    init_editor_tools()

    if args.level_paths:
        QThreadPool.globalInstance().start(lambda: _load_levels(args.level_paths))

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
