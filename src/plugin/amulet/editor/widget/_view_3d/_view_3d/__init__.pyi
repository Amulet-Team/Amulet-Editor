from __future__ import annotations

from plugin.amulet.editor.widget._view_3d._view_3d._widget import ViewportWidget

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
    "ViewportWidget",
    "ViewportWidgetIdentifier",
    "compiler_config",
    "level",
    "resource_pack",
    "selection",
]

def _get_qt_version() -> str: ...
def _init() -> None: ...

ViewportWidgetIdentifier: str
compiler_config: dict
