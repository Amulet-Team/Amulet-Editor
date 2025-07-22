#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/typing.h>

#include <optional>

#include <amulet/pybind11_extensions/py_module.hpp>

#include "_mesh_chunk.hpp"

namespace py = pybind11;
namespace pyext = Amulet::pybind11_extensions;

void init_chunk_mesher(py::module m_parent)
{
    auto m = pyext::def_subpackage(m_parent, "_chunk_mesher");
    m.def(
        "mesh_chunk",
        [](
            Amulet::Level& level,
            Amulet::AbstractOpenGLResourcePack& resource_pack,
            Amulet::DimensionId dimension_id,
            const std::int64_t cx,
            const std::int64_t cz) -> py::typing::Tuple<py::bytes, size_t> {
            std::optional<std::pair<std::string, size_t>> mesh;
            {
                py::gil_scoped_release nogil;
                mesh = Amulet::mesh_chunk(level, resource_pack, dimension_id, cx, cz);
            }
            return py::make_tuple(py::bytes(mesh->first), mesh->second);
        },
        py::arg("level"),
        py::arg("resource_pack"),
        py::arg("dimension_id"),
        py::arg("cx"),
        py::arg("cz"));
}
