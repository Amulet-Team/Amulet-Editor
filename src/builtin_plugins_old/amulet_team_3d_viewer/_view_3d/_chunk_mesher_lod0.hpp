#pragma once

#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <amulet/core/block/block.hpp>
#include <amulet/core/chunk/component/block_component.hpp>
#include <amulet/core/chunk/component/section_array_map.hpp>
#include <amulet/core/palette/block_palette.hpp>

#include <amulet/resource_pack/mesh/block/block_mesh.hpp>

#include "_resource_pack_base.hpp"

namespace Amulet {

// North (0, -1), West (-1, 0), Self (0, 0), East (1, 0), South (0, 1)
// Self pointer must not be nullptr. All others may be nullptr.
using ChunkData = std::array<const Amulet::BlockComponentData* const, 5>;

void create_lod0_chunk(
    Amulet::AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const ChunkData& all_chunk_data,
    std::string& opaque_buffer,
    std::string& translucent_buffer);

} // namespace Amulet
