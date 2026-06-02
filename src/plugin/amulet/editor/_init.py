"""Initialise all the default tools"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from amulet.level import Level

from plugin.tablericons import tablericons

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
        widget=QWidget(),
    )

    tab.activate_tool(MetadataToolIdentifier)

    tab.add_tool(
        identifier=FillToolIdentifier,
        name=("plugin.amulet.editor.tool", "fill_replace", None),
        icon_path=tablericons.outline.bucket_droplet,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=BrushToolIdentifier,
        name=("plugin.amulet.editor.tool", "brush", None),
        icon_path=tablericons.outline.brush,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=BlockEditToolIdentifier,
        name=("plugin.amulet.editor.tool", "block_editor", None),
        icon_path=tablericons.outline.cube,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=OperationToolIdentifier,
        name=("plugin.amulet.editor.tool", "operation", None),
        icon_path=tablericons.outline.brand_python,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=ImportToolIdentifier,
        name=("plugin.amulet.editor.tool", "import", None),
        icon_path=tablericons.outline_alt.file_import,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=ExportToolIdentifier,
        name=("plugin.amulet.editor.tool", "export", None),
        icon_path=tablericons.outline_alt.file_export,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=ChunkToolIdentifier,
        name=("plugin.amulet.editor.tool", "chunk", None),
        icon_path=tablericons.filled.stack_3,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=PlayerToolIdentifier,
        name=("plugin.amulet.editor.tool", "player", None),
        icon_path=tablericons.outline.user,
        widget=QWidget(),
    )

    tab.add_tool(
        identifier=ConvertToolIdentifier,
        name=("plugin.amulet.editor.tool", "convert", None),
        icon_path=tablericons.outline.arrow_big_right_lines,
        widget=QWidget(),
    )


def init_editor_tools() -> None:
    get_amulet_editor().level_tab_init.connect(_init_level_tools)

