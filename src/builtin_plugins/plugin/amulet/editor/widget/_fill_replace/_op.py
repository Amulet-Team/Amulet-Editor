from amulet.utils.lock import ThreadAccessMode, ThreadShareMode

from amulet.core.block import Block, BlockStack
from amulet.core.selection import SelectionBoxGroup, SelectionBox
from amulet.core.chunk.component import BlockComponent

from amulet.game import get_game_version

from plugin.amulet.selection import get_selection_manager
from plugin.amulet.level import get_main_level


def get_chunk_boxes(
    boxes: SelectionBoxGroup, sub_chunk_size: int
) -> dict[tuple[int, int], list[SelectionBox]]:
    chunk_boxes: dict[tuple[int, int], list[SelectionBox]] = {}

    # TODO: Can this be a generator?
    # TODO: If the selection is huge, memory will become an issue.
    #   Find intersecting boxes on a per-chunk basis?

    for box in boxes:
        min_cx = box.min_x // sub_chunk_size
        max_cx = (box.max_x - 1) // sub_chunk_size
        min_cz = box.min_z // sub_chunk_size
        max_cz = (box.max_z - 1) // sub_chunk_size
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                chunk_boxes.setdefault((cx, cz), []).append(box)

    return chunk_boxes


def fill_block(block: Block, find_block: Block | None = None) -> None:
    level = get_main_level()
    if level is None:
        return
    selection = get_selection_manager().get_selection()
    sub_chunk_size = level.sub_chunk_size
    chunk_boxes = get_chunk_boxes(selection.voxelise(), sub_chunk_size)
    with level.lock(thread_mode=(ThreadAccessMode.ReadWrite, ThreadShareMode.Unique)):
        max_version = level.max_game_version
        for (cx, cz), boxes in chunk_boxes.items():
            dimension = level.get_dimension("minecraft:overworld")
            chunk_handle = dimension.get_chunk_handle(cx, cz)
            with chunk_handle.lock(
                thread_mode=(ThreadAccessMode.ReadWrite, ThreadShareMode.SharedReadOnly)
            ):
                chunk = chunk_handle.get_chunk([BlockComponent.ComponentID])
                if isinstance(chunk, BlockComponent):
                    block_storage = chunk.block_storage
                    palette = block_storage.palette
                    sections = block_storage.sections
                    if sections.array_shape != (
                        sub_chunk_size,
                        sub_chunk_size,
                        sub_chunk_size,
                    ):
                        raise RuntimeError("Unexpected section shape")

                    target_platform = palette.version_range.platform
                    target_max_version = min(
                        max_version, palette.version_range.max_version
                    )

                    def get_converted_block(block_: Block) -> Block:
                        if (
                            block_.platform == target_platform
                            and palette.version_range.min_version
                            <= block_.version
                            <= target_max_version
                        ):
                            return block_
                        game_version = get_game_version(block_.platform, block_.version)
                        block, _, _ = game_version.block.translate(
                            target_platform, target_max_version, block_
                        )
                        if isinstance(block, Block):
                            return block
                        # TODO: How should we handle this?
                        raise RuntimeError("Block converted to an entity")

                    block = get_converted_block(block)
                    if find_block is not None:
                        find_block = get_converted_block(find_block)

                    block_index = palette.block_stack_to_index(BlockStack(block))
                    find_block_index = (
                        None
                        if find_block is None
                        else palette.block_stack_to_index(BlockStack(find_block))
                    )
                    for box in boxes:
                        min_cy = box.min_y // sub_chunk_size
                        max_cy = (box.max_y - 1) // sub_chunk_size
                        for cy in range(min_cy, max_cy + 1):
                            if cy not in sections:
                                sections.populate(cy)
                            section = sections[cy]
                            min_y = max(cy * sub_chunk_size, box.min_y)
                            max_y = min((cy + 1) * sub_chunk_size, box.max_y)
                            min_dx = box.min_x - cx * sub_chunk_size
                            max_dx = box.max_x - cx * sub_chunk_size
                            min_dy = min_y - cy * sub_chunk_size
                            max_dy = max_y - cy * sub_chunk_size
                            min_dz = box.min_z - cz * sub_chunk_size
                            max_dz = box.max_z - cz * sub_chunk_size
                            sub_section = section[
                                min_dx:max_dx, min_dy:max_dy, min_dz:max_dz
                            ]
                            if find_block_index is None:
                                sub_section.fill(block_index)
                            else:
                                sub_section[sub_section == find_block_index] = (
                                    block_index
                                )
                chunk_handle.set_chunk(chunk)
