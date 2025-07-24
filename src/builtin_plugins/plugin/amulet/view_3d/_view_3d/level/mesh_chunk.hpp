#pragma once

#include <array>
#include <string>
#include <utility>

#include <amulet/core/chunk/component/block_component.hpp>

#include <amulet/level/abc/dimension.hpp>
#include <amulet/level/abc/level.hpp>

#include <_view_3d/resource_pack/abc.hpp>

namespace Amulet {

// North (0, -1), West (-1, 0), Self (0, 0), East (1, 0), South (0, 1)
// Self pointer must not be nullptr. All others may be nullptr.
using ChunkData = std::array<const Amulet::BlockComponentData* const, 5>;

void mesh_chunk_lod0(
    AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const ChunkData& all_chunk_data,
    std::string& opaque_buffer,
    std::string& translucent_buffer);

std::pair<std::string, size_t> mesh_chunk(
    Level& level,
    AbstractOpenGLResourcePack& resource_pack,
    DimensionId dimension_id,
    const std::int64_t cx,
    const std::int64_t cz);

} // namespace Amulet
