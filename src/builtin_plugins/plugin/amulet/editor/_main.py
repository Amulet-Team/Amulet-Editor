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


def _destroy_editor() -> None:
    if home_button is not None:
        home_button.delete()
        unregister_layout(HomeLayoutID)

    if metadata_button is not None:
        metadata_button.delete()
        unregister_layout(MetadataLayoutID)

    if fill_button is not None:
        fill_button.delete()
        unregister_layout(FillLayoutId)

    if brush_button is not None:
        brush_button.delete()
        unregister_layout(BrushLayoutId)

    if block_edit_button is not None:
        block_edit_button.delete()
        unregister_layout(BlockEditLayoutId)

    if operation_button is not None:
        operation_button.delete()
        unregister_layout(OperationLayoutId)

    if import_button is not None:
        import_button.delete()
        unregister_layout(ImportLayoutId)

    if export_button is not None:
        export_button.delete()
        unregister_layout(ExportLayoutId)

    if chunk_button is not None:
        chunk_button.delete()
        unregister_layout(ChunkLayoutId)

    if player_button is not None:
        player_button.delete()
        unregister_layout(PlayerLayoutId)

    if convert_button is not None:
        convert_button.delete()
        unregister_layout(ConvertLayoutId)

    if settings_button is not None:
        settings_button.delete()

    unregister_tab_widget(HomeWidgetIdentifier)
    unregister_tab_widget(MetadataWidgetIdentifier)
    unregister_tab_widget(SelectionWidgetIdentifier)
    unregister_tab_widget(BlockEditWidgetIdentifier)
    unregister_tab_widget(BrushWidgetIdentifier)
    unregister_tab_widget(ViewportWidgetIdentifier)
    unregister_tab_widget(FillReplaceWidgetIdentifier)
    unregister_tab_widget(ImportWidgetIdentifier)
    unregister_tab_widget(ExportWidgetIdentifier)
    unregister_tab_widget(ClipboardWidgetIdentifier)
    unregister_tab_widget(PasteWidgetIdentifier)
    unregister_tab_widget(OperationWidgetIdentifier)
    unregister_tab_widget(ChunkWidgetIdentifier)
    unregister_tab_widget(PlayerWidgetIdentifier)


def _main(args: FullArgs) -> None:

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

    # Load the level
    level_path = getattr(args, "level_path", None)
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

    def _load_translations() -> None:
        _translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(editor_plugin_path[0], "_resources", "lang"),
        )

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

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)


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
