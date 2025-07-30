#include <optional>

#include <amulet/level/abc/dimension.hpp>

#include "chunk_finder.hpp"

namespace Amulet {

ChunkFinder::ChunkFinder(DimensionId dimension, int cx, int cz, int max_radius)
    : dimension(dimension)
    , cx(cx)
    , cz(cz)
    , _max_radius(max_radius)
    , _max_steps(0)
    , _steps(0)
    , _axis(Axis::North)
{
}

std::optional<std::tuple<DimensionId, int, int>> ChunkFinder::next()
{
    if ((_max_radius * 2) < _max_steps) {
        return std::nullopt;
    }

    std::tuple<DimensionId, int, int> result = { dimension, cx, cz };

    switch (_axis) {
    case Axis::North:

        if (_steps == 0) {
            _axis = Axis::East;
            cz--;
            _max_steps += 2;
            _steps = _max_steps - 1;
        } else {
            cz--;
            _steps--;
        }
        break;
    case Axis::East:
        if (_steps == 0) {
            _axis = Axis::South;
            cz++;
            _steps = _max_steps - 1;
        } else {
            cx++;
            _steps--;
        }
        break;
    case Axis::South:
        if (_steps == 0) {
            _axis = Axis::West;
            cx--;
            _steps = _max_steps - 1;
        } else {
            cz++;
            _steps--;
        }
        break;
    case Axis::West:
        if (_steps == 0) {
            _axis = Axis::North;
            cz--;
            _steps = _max_steps - 1;
        } else {
            cx--;
            _steps--;
        }
        break;
    }

    return result;
}

} // namespace Amulet
