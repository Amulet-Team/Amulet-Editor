from __future__ import annotations

import amulet.level.abc.level
import plugin.amulet.view_3d._view_3d._resource_pack_base

__all__ = ["mesh_chunk"]

def mesh_chunk(
    level: amulet.level.abc.level.Level,
    resource_pack: plugin.amulet.view_3d._view_3d._resource_pack_base.AbstractOpenGLResourcePack,
    dimension_id: str,
    cx: int,
    cz: int,
) -> tuple[bytes, int]: ...
