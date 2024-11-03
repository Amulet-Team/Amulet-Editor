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
#include <pybind11/stl.h>
#include <pybind11/typing.h>
#include <pybind11_extensions/builtins.hpp>

#include <amulet/block.hpp>
#include <amulet/chunk_components/section_array_map.hpp>
#include <amulet/mesh/block/block_mesh.hpp>
#include <amulet/palette/block_palette.hpp>
#include "_resource_pack_base.hpp"
#include "_chunk_mesher_lod0.hpp"

namespace py = pybind11;


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
			const Amulet::BlockComponentData& py_chunk_component,
			pybind11_extensions::PyObjectCpp<std::optional<Amulet::BlockComponentData>> py_north_chunk_component,
            pybind11_extensions::PyObjectCpp<std::optional<Amulet::BlockComponentData>> py_east_chunk_component,
            pybind11_extensions::PyObjectCpp<std::optional<Amulet::BlockComponentData>> py_south_chunk_component,
            pybind11_extensions::PyObjectCpp<std::optional<Amulet::BlockComponentData>> py_west_chunk_component
			) -> std::pair<py::bytes, py::bytes> {
				std::string opaque_buffer;
				std::string translucent_buffer;

				auto get_chunk_data = [&](py::object py_obj) -> const Amulet::BlockComponentData* const {
					if (py_obj.is_none()) {
						return nullptr;
					}
					else {
						return &py_obj.cast<const Amulet::BlockComponentData&>();
					}
					};

				Amulet::ChunkData all_chunk_data({
					get_chunk_data(py_north_chunk_component),
					get_chunk_data(py_west_chunk_component),
					&py_chunk_component,
					get_chunk_data(py_east_chunk_component),
					get_chunk_data(py_south_chunk_component),
					});

				{
					py::gil_scoped_release gil;
					Amulet::create_lod0_chunk(resource_pack, cx, cz, all_chunk_data, opaque_buffer, translucent_buffer);
				}

				return std::make_pair(py::bytes(opaque_buffer), py::bytes(translucent_buffer));
		},
		py::arg("resource_pack"),
		py::arg("cx"),
		py::arg("cz"),
		py::arg("block_component"),
		py::arg("north_block_component"),
		py::arg("east_block_component"),
		py::arg("south_block_component"),
		py::arg("west_block_component")
	);
}
