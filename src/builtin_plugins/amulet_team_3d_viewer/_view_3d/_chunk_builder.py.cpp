#include <stdexcept>
#include <memory>

#include <pybind11/pybind11.h>

#include <amulet/pybind11/type_hints.hpp>
#include <amulet/block.hpp>
#include <amulet/palette/block_palette.hpp>
#include <amulet/chunk_components/section_array_map.hpp>

namespace py = pybind11;


PYBIND11_MODULE(_chunk_builder, m) {
	py::module::import("amulet.palette.block_palette");
	m.def(
		"create_lod0_chunk",
		[](
			Amulet::pybind11::type_hints::PyObject<"amulet_team_3d_viewer._view_32._resource_pack"> resource_pack,
			std::shared_ptr<Amulet::IndexArray3D> arr,
			std::shared_ptr<Amulet::BlockPalette> palette
		) {
			throw std::runtime_error("NotImplemented");
		}
	);
}
