from __future__ import annotations

import amulet.core.chunk.component.block_component
import plugin.amulet.view_3d._view_3d._resource_pack_base

__all__ = ["create_lod0_chunk"]

def create_lod0_chunk(
    resource_pack: plugin.amulet.view_3d._view_3d._resource_pack_base.AbstractOpenGLResourcePack,
    cx: int,
    cz: int,
    block_component: amulet.core.chunk.component.block_component.BlockComponentData,
    north_block_component: (
        amulet.core.chunk.component.block_component.BlockComponentData | None
    ),
    east_block_component: (
        amulet.core.chunk.component.block_component.BlockComponentData | None
    ),
    south_block_component: (
        amulet.core.chunk.component.block_component.BlockComponentData | None
    ),
    west_block_component: (
        amulet.core.chunk.component.block_component.BlockComponentData | None
    ),
) -> tuple[bytes, bytes]: ...
