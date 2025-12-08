#pragma once

#include <array>
#include <string>
#include <utility>

#include <amulet/core/chunk/component/block_component.hpp>

#include <amulet/level/abc/dimension.hpp>
#include <amulet/level/abc/level.hpp>

#include <_view_3d/resource_pack/abc.hpp>

namespace Amulet {

void mesh_chunk_lod0_blocks(
    AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const Amulet::BlockStorage& self_block_data,
    const Amulet::BlockStorage* const north_block_data,
    const Amulet::BlockStorage* const east_block_data,
    const Amulet::BlockStorage* const south_block_data,
    const Amulet::BlockStorage* const west_block_data,
    std::string& opaque_buffer,
    std::string& translucent_buffer);

std::tuple<std::string, size_t, std::string, size_t> mesh_chunk(
    Level& level,
    AbstractOpenGLResourcePack& resource_pack,
    const DimensionId& dimension_id,
    const std::int64_t cx,
    const std::int64_t cz);

} // namespace Amulet
