#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <amulet/block.hpp>
#include <amulet/chunk_components/section_array_map.hpp>
#include <amulet/mesh/block/block_mesh.hpp>
#include <amulet/palette/block_palette.hpp>
#include <amulet/pybind11/type_hints.hpp>
#include "_resource_pack_base.hpp"
#include "_chunk_mesher_lod0.hpp"

namespace py = pybind11;


static void _create_lod0_chunk(
    Amulet::AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const Amulet::ChunkData& all_chunk_data,
    std::string& opaque_buffer,
    std::string& translucent_buffer)
{
    py::gil_scoped_release gil;
    Amulet::create_lod0_chunk(resource_pack, cx, cz, all_chunk_data, opaque_buffer, translucent_buffer);
} 


void init_chunk_mesher(py::module m_parent)
{
    auto m = m_parent.def_submodule("_chunk_mesher_lod0");
    py::module::import("amulet.palette.block_palette");
    m.def(
        "create_lod0_chunk",
        [](
            Amulet::AbstractOpenGLResourcePack& resource_pack,
            const std::int64_t cx,
            const std::int64_t cz,
            const Amulet::ChunkData& all_chunk_data) -> std::pair<py::bytes, py::bytes> {
            std::string opaque_buffer;
            std::string translucent_buffer;

            _create_lod0_chunk(resource_pack, cx, cz, all_chunk_data, opaque_buffer, translucent_buffer);

            return std::make_pair(py::bytes(opaque_buffer), py::bytes(translucent_buffer));
        }
    );
}
