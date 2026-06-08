"""Initialise all the default tools"""

from __future__ import annotations

from PySide6.QtCore import Qt

from amulet.level import Level

from plugin.tablericons import tablericons

from .dock.widget import register_dock_widget
from .dock.layout import (
    LayoutConfig,
    WindowConfig,
    SplitterConfig,
    WidgetStackConfig,
    WidgetConfig,
    register_layout,
)

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

from ._main_window import get_amulet_editor

MetadataToolIdentifier = "amulet.editor.metadata"
FillToolIdentifier = "amulet.editor.fill"
BrushToolIdentifier = "amulet.editor.brush"
BlockEditToolIdentifier = "amulet.editor.block_editor"
OperationToolIdentifier = "amulet.editor.operation"
ImportToolIdentifier = "amulet.editor.import"
ExportToolIdentifier = "amulet.editor.export"
ChunkToolIdentifier = "amulet.editor.chunk"
PlayerToolIdentifier = "amulet.editor.player"
ConvertToolIdentifier = "amulet.editor.convert"


def _init_level_tools(level: Level) -> None:
    tab = get_amulet_editor().get_level_tab(level)

    tab.add_tool(
        identifier=MetadataToolIdentifier,
        name=("plugin.amulet.editor.tool", "metadata", None),
        icon_path=tablericons.outline.file_info,
        widget=MetadataToolIdentifier,
    )

    tab.activate_tool(MetadataToolIdentifier)

    tab.add_tool(
        identifier=FillToolIdentifier,
        name=("plugin.amulet.editor.tool", "fill_replace", None),
        icon_path=tablericons.outline.bucket_droplet,
        widget=FillToolIdentifier,
    )

    tab.add_tool(
        identifier=BrushToolIdentifier,
        name=("plugin.amulet.editor.tool", "brush", None),
        icon_path=tablericons.outline.brush,
        widget=BrushToolIdentifier,
    )

    tab.add_tool(
        identifier=BlockEditToolIdentifier,
        name=("plugin.amulet.editor.tool", "block_editor", None),
        icon_path=tablericons.outline.cube,
        widget=BlockEditToolIdentifier,
    )

    tab.add_tool(
        identifier=OperationToolIdentifier,
        name=("plugin.amulet.editor.tool", "operation", None),
        icon_path=tablericons.outline.brand_python,
        widget=OperationToolIdentifier,
    )

    tab.add_tool(
        identifier=ImportToolIdentifier,
        name=("plugin.amulet.editor.tool", "import", None),
        icon_path=tablericons.outline_alt.file_import,
        widget=ImportToolIdentifier,
    )

    tab.add_tool(
        identifier=ExportToolIdentifier,
        name=("plugin.amulet.editor.tool", "export", None),
        icon_path=tablericons.outline_alt.file_export,
        widget=ExportToolIdentifier,
    )

    tab.add_tool(
        identifier=ChunkToolIdentifier,
        name=("plugin.amulet.editor.tool", "chunk", None),
        icon_path=tablericons.filled.stack_3,
        widget=ChunkToolIdentifier,
    )

    tab.add_tool(
        identifier=PlayerToolIdentifier,
        name=("plugin.amulet.editor.tool", "player", None),
        icon_path=tablericons.outline.user,
        widget=PlayerToolIdentifier,
    )

    tab.add_tool(
        identifier=ConvertToolIdentifier,
        name=("plugin.amulet.editor.tool", "convert", None),
        icon_path=tablericons.outline.arrow_big_right_lines,
        widget=ConvertToolIdentifier,
    )

    # settings_button = add_static_button()
    # settings_button.set_icon(tablericons.outline.settings)
    # settings_button.set_name("Settings")


def init_editor_tools() -> None:
    register_layout(
        MetadataToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                WidgetStackConfig((WidgetConfig(MetadataWidgetIdentifier),)),
            ),
            (),
        ),
    )

    register_layout(
        FillToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                SplitterConfig(
                    WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(FillReplaceWidgetIdentifier),)),
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

    register_layout(
        BrushToolIdentifier,
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

    register_layout(
        BlockEditToolIdentifier,
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

    register_layout(
        OperationToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                SplitterConfig(
                    WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                        WidgetStackConfig((WidgetConfig(OperationWidgetIdentifier),)),
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

    register_layout(
        ImportToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                SplitterConfig(
                    WidgetStackConfig((WidgetConfig(PasteWidgetIdentifier),)),
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
                        SplitterConfig(
                            WidgetStackConfig((WidgetConfig(ImportWidgetIdentifier),)),
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

    register_layout(
        ExportToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                SplitterConfig(
                    WidgetStackConfig((WidgetConfig(SelectionWidgetIdentifier),)),
                    SplitterConfig(
                        WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
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

    register_layout(
        ChunkToolIdentifier,
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

    register_layout(
        PlayerToolIdentifier,
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

    register_layout(
        ConvertToolIdentifier,
        LayoutConfig(
            WindowConfig(
                None,
                None,
                WidgetStackConfig((WidgetConfig(ViewportWidgetIdentifier),)),
            ),
            (),
        ),
    )

    register_dock_widget(MetadataWidgetIdentifier, MetadataWidget)
    register_dock_widget(SelectionWidgetIdentifier, SelectionWidget)
    register_dock_widget(BlockEditWidgetIdentifier, BlockEditWidget)
    register_dock_widget(BrushWidgetIdentifier, BrushWidget)
    register_dock_widget(ViewportWidgetIdentifier, ViewportWidget)
    register_dock_widget(FillReplaceWidgetIdentifier, FillReplaceWidget)
    register_dock_widget(ImportWidgetIdentifier, ImportWidget)
    register_dock_widget(ExportWidgetIdentifier, ExportWidget)
    register_dock_widget(ClipboardWidgetIdentifier, ClipboardWidget)
    register_dock_widget(PasteWidgetIdentifier, PasteWidget)
    register_dock_widget(OperationWidgetIdentifier, OperationWidget)
    register_dock_widget(ChunkWidgetIdentifier, ChunkWidget)
    register_dock_widget(PlayerWidgetIdentifier, PlayerWidget)

    get_amulet_editor().level_tab_init.connect(_init_level_tools)
