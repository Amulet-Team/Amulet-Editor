#pragma once

#include <cassert>
#include <optional>
#include <tuple>

#include <amulet/level/abc/dimension.hpp>

namespace Amulet {

class ChunkFinder {
public:
    ~ChunkFinder() = default;
    virtual std::optional<std::tuple<DimensionId, int, int>> next() = 0;
};

class SpiralChunkFinder : public ChunkFinder {
private:
    enum class Axis {
        East = 0,
        South = 1,
        West = 2,
        North = 3
    };

    DimensionId _dimension;
    std::int64_t _cx;
    std::int64_t _cz;
    std::int64_t _max_radius; // The maximum radius to generate to
    std::int64_t _max_steps; // Double the radius of the current step
    std::int64_t _steps; // The remaining steps before turning
    Axis _axis; // The axis we are moving in

public:
    SpiralChunkFinder(DimensionId dimension, int cx, int cz, int max_radius);

    std::optional<std::tuple<DimensionId, int, int>> next() override;
};

} // namespace Amulet
