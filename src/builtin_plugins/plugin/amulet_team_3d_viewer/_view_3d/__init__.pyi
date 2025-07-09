from __future__ import annotations

from plugin.amulet_team_3d_viewer._view_3d._widget import View3D

from . import (
    _camera,
    _canvas,
    _chunk_geometry,
    _chunk_mesher,
    _chunk_mesher_lod0,
    _key_catcher,
    _level_geometry,
    _resource_pack,
    _resource_pack_base,
    _settings,
    _textureatlas,
    _view_3d,
    _widget,
)

__all__ = ["View3D", "compiler_config"]

def _init() -> None: ...

compiler_config: dict
