from __future__ import annotations

import amulet.core.chunk.component
import amulet_team_3d_viewer._view_3d._resource_pack_base

__all__ = ["create_lod0_chunk"]

def create_lod0_chunk(
    resource_pack: amulet_team_3d_viewer._view_3d._resource_pack_base.AbstractOpenGLResourcePack,
    cx: int,
    cz: int,
    block_component: amulet.core.chunk.component.BlockComponentData,
    north_block_component: amulet.core.chunk.component.BlockComponentData | None,
    east_block_component: amulet.core.chunk.component.BlockComponentData | None,
    south_block_component: amulet.core.chunk.component.BlockComponentData | None,
    west_block_component: amulet.core.chunk.component.BlockComponentData | None,
) -> tuple[bytes, bytes]: ...
