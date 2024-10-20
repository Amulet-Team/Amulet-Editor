from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import itertools
import ctypes
import numpy
import numpy.typing

from amulet.data_types import DimensionId
from amulet.level.abc import Level, Dimension
from amulet.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.chunk import Chunk
from amulet.chunk_components import BlockComponent, BlockComponentData
from amulet.selection import SelectionGroup

from ._chunk_mesher_lod0 import create_lod0_chunk

if TYPE_CHECKING:
    from ._resource_pack import OpenGLResourcePack

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)


def _get_sub_chunks(
    level: Level, dimension: DimensionId, cx: int, cz: int, chunk: Chunk
) -> list[tuple[numpy.ndarray, int]]:
    """
    Create sub-chunk arrays that extend into the neighbour sub-chunks by one block.

    :param dimension: The dimension the chunk came from
    :param cx: The chunk x coordinate of the chunk
    :param cz: The chunk z coordinate of the chunk
    :param chunk: The chunk object
    :return: A list of tuples containing the larger block array and the location of the sub-chunk
    """
    if not isinstance(chunk, BlockComponent):
        return []
    sections = chunk.block.sections
    sub_chunks = []
    neighbour_chunks = {}
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        try:
            chunk_handle = level.get_dimension(dimension).get_chunk_handle(
                cx + dx, cz + dz
            )
            chunk = chunk_handle.get([BlockComponent.ComponentID])
            if isinstance(chunk, BlockComponent):
                neighbour_chunks[(dx, dz)] = chunk.block
        except ChunkLoadError:
            continue

    for cy, sub_chunk in sections.items():
        larger_blocks = numpy.zeros(
            sub_chunk.shape + numpy.array((2, 2, 2)), sub_chunk.dtype
        )
        # if self._limit_bounds:
        #     sub_chunk_box = SelectionBox.create_sub_chunk_box(cx, cy, cz)
        #     if level.bounds(self.dimension).intersects(sub_chunk_box):
        #         boxes = level.bounds(self.dimension).intersection(
        #             sub_chunk_box
        #         )
        #         for box in boxes.selection_boxes:
        #             larger_blocks[1:-1, 1:-1, 1:-1][
        #                 box.sub_chunk_slice(self.cx, cy, self.cz)
        #             ] = sub_chunk[box.sub_chunk_slice(self.cx, cy, self.cz)]
        #     else:
        #         continue
        # else:
        #     larger_blocks[1:-1, 1:-1, 1:-1] = sub_chunk
        larger_blocks[1:-1, 1:-1, 1:-1] = sub_chunk
        for chunk_offset, neighbour_blocks in neighbour_chunks.items():
            neighbour_sections = neighbour_blocks.sections
            if cy not in neighbour_sections:
                continue
            if chunk_offset == (-1, 0):
                larger_blocks[0, 1:-1, 1:-1] = neighbour_sections[cy][-1, :, :]
            elif chunk_offset == (1, 0):
                larger_blocks[-1, 1:-1, 1:-1] = neighbour_sections[cy][0, :, :]
            elif chunk_offset == (0, -1):
                larger_blocks[1:-1, 1:-1, 0] = neighbour_sections[cy][:, :, -1]
            elif chunk_offset == (0, 1):
                larger_blocks[1:-1, 1:-1, -1] = neighbour_sections[cy][:, :, 0]
        if cy - 1 in sections:
            larger_blocks[1:-1, 0, 1:-1] = sections[cy - 1][:, -1, :]
        if cy + 1 in sections:
            larger_blocks[1:-1, -1, 1:-1] = sections[cy + 1][:, 0, :]
        sub_chunks.append((larger_blocks, cy * 16))
    return sub_chunks


def _create_chunk_plane(height: float) -> tuple[numpy.ndarray, numpy.ndarray]:
    box = numpy.array([(0, height, 0), (16, height, 16)])
    _box_coordinates = numpy.array(list(itertools.product(*box.T.tolist())))
    _cube_face_lut = numpy.array(
        [  # This maps to the verticies used (defined in cube_vert_lut)
            0,
            4,
            5,
            1,
            3,
            7,
            6,
            2,
        ]
    )
    box = box.ravel()
    _texture_index = numpy.array([0, 2, 3, 5, 0, 2, 3, 5], numpy.uint32)
    _uv_slice = numpy.array([0, 1, 2, 1, 2, 3, 0, 3] * 2, dtype=numpy.uint32).reshape(
        (-1, 8)
    ) + numpy.arange(0, 8, 4).reshape((-1, 1))

    _tri_face = numpy.array([0, 1, 2, 0, 2, 3] * 2, numpy.uint32).reshape(
        (-1, 6)
    ) + numpy.arange(0, 8, 4).reshape((-1, 1))
    return (
        _box_coordinates[_cube_face_lut[_tri_face]].reshape((-1, 3)),
        box[_texture_index[_uv_slice]].reshape(-1, 2)[_tri_face, :].reshape((-1, 2)),
    )


def _create_grid(
    level_bounds: SelectionGroup,
    resource_pack: OpenGLResourcePack,
    texture_namespace: str,
    texture_path: str,
    draw_floor: bool,
    draw_ceil: bool,
    tint: tuple[float, float, float],
) -> numpy.typing.NDArray[numpy.float32]:
    vert_len = 12
    plane: numpy.ndarray = numpy.ones(
        (vert_len * 12 * (draw_floor + draw_ceil)),
        dtype=numpy.float32,
    ).reshape((-1, vert_len))
    if draw_floor:
        plane[:12, :3], plane[:12, 3:5] = _create_chunk_plane(level_bounds.min_y - 0.01)
        if draw_ceil:
            plane[12:, :3], plane[12:, 3:5] = _create_chunk_plane(
                level_bounds.max_y + 0.01
            )
    elif draw_ceil:
        plane[:12, :3], plane[:12, 3:5] = _create_chunk_plane(level_bounds.max_y + 0.01)

    plane[:, 5:9] = resource_pack.texture_bounds(
        resource_pack.get_texture_path(texture_namespace, texture_path)
    )
    plane[:, 9:12] = tint
    return plane


def _get_empty_geometry(
    level_bounds: SelectionGroup,
    resource_pack: OpenGLResourcePack,
    cx: int,
    cz: int,
) -> bytes:
    return (
        _create_grid(
            level_bounds,
            resource_pack,
            "amulet",
            "amulet_ui/chunk_grid_null",
            True,
            True,
            # (1, 1, 1) if (cx + cz) % 2 else (0.8, 0.8, 0.8),
            (0.1, 0.1, 0.1) if (cx + cz) % 2 else (0.0, 0.0, 0.0),
        )
        .ravel()
        .tobytes()
    )


def _get_error_geometry(
    level_bounds: SelectionGroup,
    resource_pack: OpenGLResourcePack,
    cx: int,
    cz: int,
) -> bytes:
    return (
        _create_grid(
            level_bounds,
            resource_pack,
            "amulet",
            "amulet_ui/chunk_grid_error",
            True,
            True,
            # (1, 1, 1) if (cx + cz) % 2 else (0.8, 0.8, 0.8),
            (0.5, 0.5, 0.5) if (cx + cz) % 2 else (0.6, 0.6, 0.6),
        )
        .ravel()
        .tobytes()
    )


def _get_temp_geometry(
    level_bounds: SelectionGroup,
    resource_pack: OpenGLResourcePack,
    cx: int,
    cz: int,
) -> bytes:
    return (
        _create_grid(
            level_bounds,
            resource_pack,
            "amulet",
            "amulet_ui/chunk_grid_error",
            True,
            True,
            (1, 1, 1) if (cx + cz) % 2 else (0.8, 0.8, 0.8),
        )
        .ravel()
        .tobytes()
    )


def get_block_component(dimension: Dimension, cx: int, cz: int) -> BlockComponentData | None:
    try:
        chunk = dimension.get_chunk_handle(cx, cz).get([BlockComponent.ComponentID])
    except ChunkLoadError:
        return None
    else:
        if isinstance(chunk, BlockComponent):
            return chunk.block
        else:
            return None


def mesh_chunk(
    level: Level,
    resource_pack: OpenGLResourcePack,
    dimension_id: DimensionId,
    cx: int,
    cz: int,
) -> tuple[bytes, int]:
    with level.lock_shared():
        if not level.is_open():
            raise RuntimeError("The level has been closed.")
        dimension = level.get_dimension(dimension_id)

        try:
            chunk = dimension.get_chunk_handle(cx, cz).get([BlockComponent.ComponentID])
        except ChunkDoesNotExist:
            log.debug(f"Chunk {dimension_id}, {cx}, {cz} does not exist")
            buffer = _get_empty_geometry(dimension.bounds(), resource_pack, cx, cz)
        except ChunkLoadError:
            log.exception(
                f"Error loading chunk {dimension_id}, {cx}, {cz}", exc_info=True
            )
            buffer = _get_error_geometry(dimension.bounds(), resource_pack, cx, cz)
        else:
            if isinstance(chunk, BlockComponent):
                log.debug(f"Creating geometry for chunk {dimension_id}, {cx}, {cz}")
                opaque_buffer, translucent_buffer = create_lod0_chunk(
                    resource_pack,
                    cx,
                    cz,
                    chunk.block,
                    get_block_component(dimension, cx, cz - 1),
                    get_block_component(dimension, cx + 1, cz),
                    get_block_component(dimension, cx, cz + 1),
                    get_block_component(dimension, cx - 1, cz),
                )
                buffer = opaque_buffer + translucent_buffer
            else:
                log.debug(
                    f"Chunk {dimension_id}, {cx}, {cz} does not implement BlockComponent."
                )
                buffer = b""

        log.debug(f"Generated array for {dimension_id}, {cx}, {cz}")

        vertex_count = len(buffer) // (12 * FloatSize)
        log.debug(f"Generated chunk {dimension_id}, {cx}, {cz}")
        return buffer, vertex_count
