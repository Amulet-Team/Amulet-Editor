#pragma once

#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <amulet/block.hpp>
#include <amulet/chunk_components/section_array_map.hpp>
#include <amulet/mesh/block/block_mesh.hpp>
#include <amulet/palette/block_palette.hpp>

#include "_resource_pack_base.hpp"

namespace Amulet {

void create_lod0_chunk(
    Amulet::AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const Amulet::SectionArrayMap& sections,
    const Amulet::BlockPalette& palette,
    std::string& opaque_buffer,
    std::string& translucent_buffer);

} // namespace Amulet
