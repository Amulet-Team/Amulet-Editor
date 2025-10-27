from __future__ import annotations

from argparse import ArgumentParser
import logging
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QLocale, Qt

from amulet.level import get_level
from amulet.level.loader import LevelLoaderPathToken

from amulet.app import __version__
from amulet.app.cli import FullArgs, Command
from amulet.app.resource import get_resource_path
from amulet.app.exception import CatchExceptionDialog
from amulet.app.localisation import Translator, locale_changed

from plugin.tablericons import tablericons
from plugin.amulet.level import get_main_level, set_main_level

from . import __path__ as editor_plugin_path
from .window._main_window import (
    init_main_window,
    get_main_window,
    destroy_main_window,
    ButtonProxy,
)
from .widget._home import HomeWidget, HomeWidgetIdentifier
from .widget._level_info import (
    LevelInfoWidget,
    LevelInfoWidgetIdentifier,
)
from .widget._selection import (
    SelectionWidget,
    SelectionWidgetIdentifier,
)
from .widget._view_3d import View3DWidget, View3DWidgetIdentifier
from .widget._block_inspect import BlockEditWidget, BlockEditWidgetIdentifier
from .widget._fill_replace import FillReplaceWidget, FillReplaceWidgetIdentifier
from .widget import register_tab_widget, unregister_tab_widget
from .layout import (
    register_layout,
    unregister_layout,
    LayoutConfig,
    WindowConfig,
    SplitterConfig,
    WidgetStackConfig,
    WidgetConfig,
    create_layout_button,
)
from ._signal import init_editor, destroy_editor

log = logging.getLogger(__name__)


# Qt only weekly references this. We must hold a strong reference to stop it getting garbage collected
_translator: Translator | None = None

HomeLayoutID = "amulet.home"
home_button: ButtonProxy | None = None

LevelInfoLayoutID = "amulet.level_info"
level_info_button: ButtonProxy | None = None

SelectLayoutId = "amulet.editor"
select_button: ButtonProxy | None = None

FillLayoutId = "amulet.fill"
fill_button: ButtonProxy | None = None

BrushLayoutId = "amulet.brush"
brush_button: ButtonProxy | None = None

BlockEditLayoutId = "amulet.block_editor"
block_edit_button: ButtonProxy | None = None

ChunkLayoutId = "amulet.chunk"
chunk_button: ButtonProxy | None = None

ConvertLayoutId = "amulet.convert"
convert_button: ButtonProxy | None = None


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
        directory=os.path.join(editor_plugin_path[0], "_resources", "lang"),
    )


def _init_editor() -> None:
    global home_button
    global level_info_button
    global select_button
    global fill_button
    global brush_button
    global block_edit_button
    global chunk_button
    global convert_button

    register_tab_widget(HomeWidgetIdentifier, HomeWidget)
    register_tab_widget(LevelInfoWidgetIdentifier, LevelInfoWidget)
    register_tab_widget(SelectionWidgetIdentifier, SelectionWidget)
    register_tab_widget(BlockEditWidgetIdentifier, BlockEditWidget)
    register_tab_widget(View3DWidgetIdentifier, View3DWidget)
    register_tab_widget(FillReplaceWidgetIdentifier, FillReplaceWidget)

    register_layout(
        HomeLayoutID,
        LayoutConfig(
            WindowConfig(
                None, None, WidgetStackConfig((WidgetConfig(HomeWidgetIdentifier),))
            ),
            (),
        ),
    )

    # Set up the home button
    home_button = create_layout_button(HomeLayoutID)
    home_button.set_icon(tablericons.outline.home)
    home_button.set_name("Home")

    if get_main_level() is None:
        # Make the home layout active by clicking the button
        home_button.click()
    else:
        register_layout(
            LevelInfoLayoutID,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(LevelInfoWidgetIdentifier),)),
                ),
                (),
            ),
        )

        # Set up the home button
        level_info_button = create_layout_button(LevelInfoLayoutID)
        level_info_button.set_icon(tablericons.outline.file_info)
        level_info_button.set_name("Level Info")
        level_info_button.click()

        register_layout(
            SelectLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        # Set up the 3D View button
        select_button = create_layout_button(SelectLayoutId)
        select_button.set_icon(tablericons.outline.cube_3d_sphere)
        select_button.set_name("Select")

        register_layout(
            FillLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                            WidgetStackConfig(
                                (WidgetConfig(FillReplaceWidgetIdentifier),)
                            ),
                            Qt.Orientation.Horizontal,
                            0.9,
                        ),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        fill_button = create_layout_button(FillLayoutId)
        fill_button.set_icon(tablericons.outline.bucket_droplet)
        fill_button.set_name("Fill")

        register_layout(
            BrushLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        brush_button = create_layout_button(BrushLayoutId)
        brush_button.set_icon(tablericons.outline.brush)
        brush_button.set_name("Brush")

        register_layout(
            BlockEditLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(BlockEditWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        block_edit_button = create_layout_button(BlockEditLayoutId)
        block_edit_button.set_icon(tablericons.outline.cube)
        block_edit_button.set_name("Block Editor")

        register_layout(
            ChunkLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                ),
                (),
            ),
        )

        chunk_button = create_layout_button(ChunkLayoutId)
        chunk_button.set_icon(tablericons.filled.stack_3)
        chunk_button.set_name("Chunk")

        register_layout(
            ConvertLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(View3DWidgetIdentifier),)),
                ),
                (),
            ),
        )

        convert_button = create_layout_button(ConvertLayoutId)
        convert_button.set_icon(tablericons.filled.arrow_big_right_lines)
        convert_button.set_name("Convert")


def _destroy_editor() -> None:
    if home_button is not None:
        home_button.delete()
        unregister_layout(HomeLayoutID)

    if level_info_button is not None:
        level_info_button.delete()
        unregister_layout(LevelInfoLayoutID)

    if select_button is not None:
        select_button.delete()
        unregister_layout(SelectLayoutId)

    if brush_button is not None:
        brush_button.delete()
        unregister_layout(BrushLayoutId)

    if chunk_button is not None:
        chunk_button.delete()
        unregister_layout(ChunkLayoutId)

    if convert_button is not None:
        convert_button.delete()
        unregister_layout(ConvertLayoutId)

    if block_edit_button is not None:
        block_edit_button.delete()
        unregister_layout(BlockEditLayoutId)

    if fill_button is not None:
        fill_button.delete()
        unregister_layout(FillLayoutId)

    unregister_tab_widget(HomeWidgetIdentifier)
    unregister_tab_widget(LevelInfoWidgetIdentifier)
    unregister_tab_widget(SelectionWidgetIdentifier)
    unregister_tab_widget(BlockEditWidgetIdentifier)
    unregister_tab_widget(View3DWidgetIdentifier)
    unregister_tab_widget(FillReplaceWidgetIdentifier)


def _main(args: FullArgs) -> None:
    global _translator

    # Initialise the application
    _init_app()

    # Load the level
    level_path = args.level_path
    if level_path is None:
        set_main_level(None)
    else:
        log.debug("Loading level.")
        with CatchExceptionDialog(
            f"Failed loading level at path {level_path}", suppress=False
        ):
            level = get_level(
                LevelLoaderPathToken(level_path)
            )  # TODO: make this generic
            level.open()
            set_main_level(level)

    # Load the translations
    _translator = Translator()
    _load_translations()
    QApplication.installTranslator(_translator)
    locale_changed.connect(_load_translations)

    # Initialise the main window
    init_main_window()

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
