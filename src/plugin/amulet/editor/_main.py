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
from amulet.app.app import app_created
from amulet.app.style import set_style
from amulet.app.invoke import invoke

from . import __path__ as editor_plugin_path
from .window._main_window import (
    init_main_window,
    get_main_window,
    ButtonProxy,
    add_static_button,
)
from .widget._home import HomeWidget, HomeWidgetIdentifier
from .widget._metadata import MetadataWidget, MetadataWidgetIdentifier
from .widget._selection import SelectionWidget, SelectionWidgetIdentifier
from .widget._view_3d import ViewportWidget, ViewportWidgetIdentifier
from .widget._block_inspect import BlockEditWidget, BlockEditWidgetIdentifier
from .widget._brush import BrushWidget, BrushWidgetIdentifier
from .widget._fill_replace import FillReplaceWidget, FillReplaceWidgetIdentifier
from .widget._import import ImportWidget, ImportWidgetIdentifier
from .widget._export import ExportWidget, ExportWidgetIdentifier
from .widget._clipboard import ClipboardWidget, ClipboardWidgetIdentifier
from .widget._paste import PasteWidget, PasteWidgetIdentifier
from .widget._operation import OperationWidget, OperationWidgetIdentifier
from .widget._chunk import ChunkWidget, ChunkWidgetIdentifier
from .widget._player import PlayerWidget, PlayerWidgetIdentifier
from .widget import register_tab_widget
from .layout import (
    register_layout,
    LayoutConfig,
    WindowConfig,
    SplitterConfig,
    WidgetStackConfig,
    WidgetConfig,
    create_layout_button,
)
from ._signal import init_editor, destroy_editor
from ._window import init_and_show_editor, get_amulet_editor_api
from ._window import init_and_show_editor, get_amulet_editor

log = logging.getLogger(__name__)

HomeLayoutID = "amulet.home"
home_button: ButtonProxy | None = None

MetadataLayoutID = "amulet.metadata"
metadata_button: ButtonProxy | None = None

FillLayoutId = "amulet.fill"
fill_button: ButtonProxy | None = None

BrushLayoutId = "amulet.brush"
brush_button: ButtonProxy | None = None

BlockEditLayoutId = "amulet.block_editor"
block_edit_button: ButtonProxy | None = None

OperationLayoutId = "amulet.operation"
operation_button: ButtonProxy | None = None

ImportLayoutId = "amulet.import"
import_button: ButtonProxy | None = None

ExportLayoutId = "amulet.export"
export_button: ButtonProxy | None = None

ChunkLayoutId = "amulet.chunk"
chunk_button: ButtonProxy | None = None

PlayerLayoutId = "amulet.player"
player_button: ButtonProxy | None = None

ConvertLayoutId = "amulet.convert"
convert_button: ButtonProxy | None = None

settings_button: ButtonProxy | None = None


def _init_editor() -> None:
    global home_button
    global metadata_button
    global fill_button
    global brush_button
    global block_edit_button
    global import_button
    global export_button
    global chunk_button
    global player_button
    global convert_button
    global settings_button

    register_tab_widget(HomeWidgetIdentifier, HomeWidget)
    register_tab_widget(MetadataWidgetIdentifier, MetadataWidget)
    register_tab_widget(SelectionWidgetIdentifier, SelectionWidget)
    register_tab_widget(BlockEditWidgetIdentifier, BlockEditWidget)
    register_tab_widget(BrushWidgetIdentifier, BrushWidget)
    register_tab_widget(ViewportWidgetIdentifier, ViewportWidget)
    register_tab_widget(FillReplaceWidgetIdentifier, FillReplaceWidget)
    register_tab_widget(ImportWidgetIdentifier, ImportWidget)
    register_tab_widget(ExportWidgetIdentifier, ExportWidget)
    register_tab_widget(ClipboardWidgetIdentifier, ClipboardWidget)
    register_tab_widget(PasteWidgetIdentifier, PasteWidget)
    register_tab_widget(OperationWidgetIdentifier, OperationWidget)
    register_tab_widget(ChunkWidgetIdentifier, ChunkWidget)
    register_tab_widget(PlayerWidgetIdentifier, PlayerWidget)

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
            MetadataLayoutID,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(MetadataWidgetIdentifier),)),
                ),
                (),
            ),
        )

        # Set up the home button
        metadata_button = create_layout_button(MetadataLayoutID)
        metadata_button.set_icon(tablericons.outline.file_info)
        metadata_button.set_name("Metadata")
        metadata_button.click()

        register_layout(
            FillLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig(
                                (WidgetConfig(ViewportWidgetIdentifier),)
                            ),
                            WidgetStackConfig(
                                (WidgetConfig(FillReplaceWidgetIdentifier),)
                            ),
                            Qt.Orientation.Horizontal,
                            8 / 9,
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
        fill_button.set_name("Fill/Replace")

        register_layout(
            BrushLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(BrushWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
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
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
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
            OperationLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig(
                                (WidgetConfig(ViewportWidgetIdentifier),)
                            ),
                            WidgetStackConfig(
                                (WidgetConfig(OperationWidgetIdentifier),)
                            ),
                            Qt.Orientation.Horizontal,
                            8 / 9,
                        ),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        operation_button = create_layout_button(OperationLayoutId)
        operation_button.set_icon(tablericons.outline.brand_python)
        operation_button.set_name("Operation")

        register_layout(
            ImportLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(PasteWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig(
                                (WidgetConfig(ViewportWidgetIdentifier),)
                            ),
                            SplitterConfig(
                                WidgetStackConfig(
                                    (WidgetConfig(ImportWidgetIdentifier),)
                                ),
                                WidgetStackConfig(
                                    (WidgetConfig(ClipboardWidgetIdentifier),)
                                ),
                                Qt.Orientation.Vertical,
                                0.5,
                            ),
                            Qt.Orientation.Horizontal,
                            0.8,
                        ),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        import_button = create_layout_button(ImportLayoutId)
        import_button.set_icon(tablericons.outline_alt.file_import)
        import_button.set_name("Import")

        register_layout(
            ExportLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig(
                                (WidgetConfig(ViewportWidgetIdentifier),)
                            ),
                            WidgetStackConfig((WidgetConfig(ExportWidgetIdentifier),)),
                            Qt.Orientation.Horizontal,
                            8 / 9,
                        ),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        export_button = create_layout_button(ExportLayoutId)
        export_button.set_icon(tablericons.outline_alt.file_export)
        export_button.set_name("Export")

        register_layout(
            ChunkLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(ChunkWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        chunk_button = create_layout_button(ChunkLayoutId)
        chunk_button.set_icon(tablericons.filled.stack_3)
        chunk_button.set_name("Chunk")

        register_layout(
            PlayerLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(PlayerWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                        Qt.Orientation.Horizontal,
                        0.1,
                    ),
                ),
                (),
            ),
        )

        player_button = create_layout_button(PlayerLayoutId)
        player_button.set_icon(tablericons.outline.user)
        player_button.set_name("Player")

        register_layout(
            ConvertLayoutId,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                ),
                (),
            ),
        )

        convert_button = create_layout_button(ConvertLayoutId)
        convert_button.set_icon(tablericons.outline.arrow_big_right_lines)
        convert_button.set_name("Convert")

    settings_button = add_static_button()
    settings_button.set_icon(tablericons.outline.settings)
    settings_button.set_name("Settings")


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
    app = QApplication()
    app_created.emit()
    app.setApplicationName("Amulet Editor")
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

    init_and_show_editor()

    if args.level_paths:
        QThreadPool.globalInstance().start(lambda: _load_levels(args.level_paths))

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
