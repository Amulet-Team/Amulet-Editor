from __future__ import annotations

from argparse import ArgumentParser
import logging

from amulet.level import get_level
from amulet.level.loader import LevelLoaderPathToken

from ._main_window import get_main_window, destroy_main_window
from amulet_editor.models.plugin import PluginV1
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.application.command import (
    Command,
    register_command,
    unregister_command,
)
from amulet_editor.data.level import _level

log = logging.getLogger(__name__)


def main(args) -> None:

    if args.command is None:
        _level.level = None
    else:
        log.debug("Loading level.")
        level_path = args.level_path
        with DisplayException(f"Failed loading level at path {level_path}"):
            _level.level = level = get_level(
                LevelLoaderPathToken(level_path)
            )  # TODO: make this generic
            level.open()
    get_main_window().showMaximized()


def init_argparse(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--level_path",
        type=str,
        help="The Minecraft world or structure to open. Default opens no level",
        action="store",
        dest="level_path",
        default=None,
    )


_editor_command: Command | None = None


def load_plugin() -> None:
    global _editor_command
    _editor_command = Command(
        name="main",
        main_func=main,
        init_argparse=init_argparse,
    )
    register_command(_editor_command)


def unload_plugin() -> None:
    # destroy_main_window()
    unregister_command(_editor_command)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
