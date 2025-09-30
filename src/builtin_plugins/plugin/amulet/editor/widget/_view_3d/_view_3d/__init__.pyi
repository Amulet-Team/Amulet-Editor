from __future__ import annotations

from plugin.amulet.editor.widget._view_3d._view_3d._widget import View3DWidget

from . import (
    _camera,
    _canvas,
    _key_catcher,
    _settings,
    _view_3d,
    _widget,
    level,
    resource_pack,
    selection,
)

__all__: list[str] = [
    "View3DWidget",
    "View3DWidgetIdentifier",
    "compiler_config",
    "level",
    "resource_pack",
    "selection",
]

def _get_qt_version() -> str: ...
def _init() -> None: ...

View3DWidgetIdentifier: str
compiler_config: dict
