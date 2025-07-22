#pragma once

#include <string>
#include <utility>

#include <amulet/level/abc/level.hpp>
#include <amulet/level/abc/dimension.hpp>

#include "_resource_pack_base.hpp"

namespace Amulet {

std::pair<std::string, size_t> mesh_chunk(
	Level& level,
    AbstractOpenGLResourcePack& resource_pack,
    DimensionId dimension_id,
    const std::int64_t cx,
    const std::int64_t cz);

} // namespace Amulet
