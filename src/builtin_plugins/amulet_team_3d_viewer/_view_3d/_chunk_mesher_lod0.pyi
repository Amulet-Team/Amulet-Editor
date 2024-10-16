from __future__ import annotations

import amulet.chunk_components
import amulet.palette.block_palette
import amulet_team_3d_viewer._view_3d._resource_pack_base

__all__ = ["create_lod0_chunk"]

def create_lod0_chunk(
    arg0: amulet_team_3d_viewer._view_3d._resource_pack_base.AbstractOpenGLResourcePack,
    arg1: int,
    arg2: int,
    arg3: amulet.chunk_components.SectionArrayMap,
    arg4: amulet.palette.block_palette.BlockPalette,
) -> tuple[bytes, bytes]: ...