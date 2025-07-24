from __future__ import annotations

import typing

import amulet.level.abc.level
import plugin.amulet.view_3d._view_3d.resource_pack.abc

__all__ = ["mesh_chunk"]

def mesh_chunk(
    level: amulet.level.abc.level.Level,
    resource_pack: plugin.amulet.view_3d._view_3d.resource_pack.abc.AbstractOpenGLResourcePack,
    dimension_id: str,
    cx: typing.SupportsInt,
    cz: typing.SupportsInt,
) -> tuple[bytes, int]: ...
