from __future__ import annotations

import amulet.chunk_components
import amulet_team_3d_viewer._view_3d._resource_pack_base

__all__ = ["create_lod0_chunk"]

def create_lod0_chunk(
    resource_pack: amulet_team_3d_viewer._view_3d._resource_pack_base.AbstractOpenGLResourcePack,
    cx: int,
    cz: int,
    block_component: amulet.chunk_components.BlockComponentData,
    north_block_component: amulet.chunk_components.BlockComponentData | None,
    east_block_component: amulet.chunk_components.BlockComponentData | None,
    south_block_component: amulet.chunk_components.BlockComponentData | None,
    west_block_component: amulet.chunk_components.BlockComponentData | None,
) -> tuple[bytes, bytes]: ...
