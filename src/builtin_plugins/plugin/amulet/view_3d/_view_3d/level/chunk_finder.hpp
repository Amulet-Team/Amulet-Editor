#pragma once

#include <cassert>
#include <optional>
#include <tuple>

#include <amulet/level/abc/dimension.hpp>

namespace Amulet {

class ChunkFinder {
public:
    DimensionId dimension;
    std::int64_t cx;
    std::int64_t cz;

    ChunkFinder(DimensionId dimension, int cx, int cz, int max_radius);

    std::optional<std::tuple<DimensionId, int, int>> next();

private:
    enum class Axis {
        East = 0,
        South = 1,
        West = 2,
        North = 3
    };

    std::int64_t _max_radius; // The maximum radius to generate to
    std::int64_t _max_steps; // Double the radius of the current step
    std::int64_t _steps; // The remaining steps before turning
    Axis _axis; // The axis we are moving in
};

} // namespace Amulet
