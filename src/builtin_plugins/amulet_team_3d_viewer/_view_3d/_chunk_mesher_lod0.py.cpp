#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <amulet/block.hpp>
#include <amulet/chunk_components/section_array_map.hpp>
#include <amulet/palette/block_palette.hpp>
#include <amulet/pybind11/type_hints.hpp>

namespace py = pybind11;

void create_lod0_subchunk(
    const std::int64_t cx,
    const std::int64_t cy,
    const std::int64_t cz,
    const Amulet::IndexArray3D& section,
    const Amulet::BlockPalette& palette,
    std::string& opaque_buffer,
    std::string& translucent_buffer)
{
}

void create_lod0_chunk(
    const std::int64_t cx,
    const std::int64_t cz,
    const Amulet::SectionArrayMap& sections,
    const Amulet::BlockPalette& palette,
    std::string& opaque_buffer,
    std::string& translucent_buffer)
{
    // Release the GIL so this can run in parallel.
    py::gil_scoped_release release;

    for (const auto& section : sections.get_arrays()) {
        create_lod0_subchunk(cx, section.first, cz, *section.second, palette, opaque_buffer, translucent_buffer);
    }
}

PYBIND11_MODULE(_chunk_builder, m)
{
    py::module::import("amulet.palette.block_palette");
    m.def(
        "create_lod0_chunk",
        [](
            Amulet::pybind11::type_hints::PyObjectStr<"amulet_team_3d_viewer._view_3d._resource_pack.OpenGLResourcePack"> resource_pack,
            const std::int64_t cx,
            const std::int64_t cz,
            const Amulet::SectionArrayMap& sections,
            const Amulet::BlockPalette& palette) -> std::pair<py::bytes, py::bytes> {
            std::string opaque_buffer;
            std::string translucent_buffer;
            create_lod0_chunk(cx, cz, sections, palette, opaque_buffer, translucent_buffer);
            return std::make_pair(py::bytes(opaque_buffer), py::bytes(translucent_buffer));
        });
}
