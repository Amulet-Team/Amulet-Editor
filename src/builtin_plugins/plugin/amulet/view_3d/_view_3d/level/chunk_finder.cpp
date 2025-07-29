#include <optional>

#include <amulet/level/abc/dimension.hpp>

#include "chunk_finder.hpp"

namespace Amulet {

SpiralChunkFinder::SpiralChunkFinder(DimensionId dimension, int cx, int cz, int max_radius)
    : _dimension(dimension)
    , _cx(cx)
    , _cz(cz)
    , _max_radius(max_radius)
    , _max_steps(0)
    , _steps(0)
    , _axis(Axis::North)
{
}

std::optional<std::tuple<DimensionId, int, int>> SpiralChunkFinder::next()
{
    if ((_max_radius * 2) < _max_steps) {
        return std::nullopt;
    }

    std::tuple<DimensionId, int, int> result = { _dimension, _cx, _cz };

    switch (_axis) {
    case Axis::North:

        if (_steps == 0) {
            _axis = Axis::East;
            _cz--;
            _max_steps += 2;
            _steps = _max_steps - 1;
        } else {
            _cz--;
            _steps--;
        }
        break;
    case Axis::East:
        if (_steps == 0) {
            _axis = Axis::South;
            _cz++;
            _steps = _max_steps - 1;
        } else {
            _cx++;
            _steps--;
        }
        break;
    case Axis::South:
        if (_steps == 0) {
            _axis = Axis::West;
            _cx--;
            _steps = _max_steps - 1;
        } else {
            _cz++;
            _steps--;
        }
        break;
    case Axis::West:
        if (_steps == 0) {
            _axis = Axis::North;
            _cz--;
            _steps = _max_steps - 1;
        } else {
            _cx--;
            _steps--;
        }
        break;
    }

    return result;
}

} // namespace Amulet
