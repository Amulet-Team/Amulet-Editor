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

namespace py = pybind11;

void create_lod0_subchunk(
    const std::int64_t cx,
    const std::int64_t cy,
    const std::int64_t cz,
    const Amulet::IndexArray3D& section,
    const Amulet::BlockPalette& palette,
    std::string& opaque_buffer,
    std::string& translucent_buffer,
    std::function<const Amulet::BlockMesh(const Amulet::BlockStack&)> get_block_mesh,
    std::function<const std::tuple<float, float, float, float>(const std::string&)> get_texture_bounds)
{
    const auto& section_shape = section.get_shape();
    const std::int32_t x_shape = std::get<0>(section_shape);
    const std::int32_t y_shape = std::get<1>(section_shape);
    const std::int32_t z_shape = std::get<2>(section_shape);
    const auto x_span = y_shape * z_shape;
    const auto& section_buffer = section.get_buffer();

    std::map<std::uint32_t, Amulet::BlockMesh> block_meshes;

    auto get_block_mesh2 = [&](const std::uint32_t block_id) -> const Amulet::BlockMesh& {
        const auto& it = block_meshes.find(block_id);
        if (it == block_meshes.end()) {
            return block_meshes.emplace(
                                   block_id,
                                   get_block_mesh(*palette.index_to_block_stack(block_id)))
                .first->second;
        } else {
            return it->second;
        }
    };

    for (std::int32_t x = 0; x < x_shape; x++) {
        for (std::int32_t y = 0; y < y_shape; y++) {
            for (std::int32_t z = 0; z < z_shape; z++) {
                const auto& block_id = section_buffer[x * x_span + y * z_shape + z];
                const auto& mesh = get_block_mesh2(block_id);

                auto add_part = [&](const Amulet::BlockMeshPart& part) {
                    auto add_vert = [&](size_t index, const std::tuple<float, float, float, float>& bounds) {
                        const auto& vert = part.verts[index];
                        size_t buffer_size = opaque_buffer.size();
                        opaque_buffer.resize(buffer_size + sizeof(float) * 12);
                        float* buffer = reinterpret_cast<float*>(&opaque_buffer[buffer_size]);
                        buffer[0] = vert.coord.x + x;
                        buffer[1] = cy * y_shape + y + vert.coord.y;
                        buffer[2] = vert.coord.z + z;
                        buffer[3] = vert.texture_coord.x;
                        buffer[4] = vert.texture_coord.y;
                        buffer[5] = std::get<0>(bounds);
                        buffer[6] = std::get<1>(bounds);
                        buffer[7] = std::get<2>(bounds);
                        buffer[8] = std::get<3>(bounds);
                        buffer[9] = vert.tint.x;
                        buffer[10] = vert.tint.y;
                        buffer[11] = vert.tint.z;
                    };
                    for (const auto& triangle : part.triangles) {
                        const auto bounds = get_texture_bounds(mesh.textures[triangle.texture_index]);
                        add_vert(triangle.vert_index_a, bounds);
                        add_vert(triangle.vert_index_b, bounds);
                        add_vert(triangle.vert_index_c, bounds);
                    }
                };

                auto add_part_conditional = [&](const std::optional<Amulet::BlockMeshPart>& part, std::int32_t dx, std::int32_t dy, std::int32_t dz) {
                    if (!part) {
                        return;
                    }
                    std::int32_t x2 = x + dx;
                    std::int32_t y2 = y + dy;
                    std::int32_t z2 = z + dz;

                    if (x2 < 0) {
                        // TODO
                    } else if (y2 < 0) {
                        // TODO
                    } else if (z2 < 0) {
                        // TODO
                    } else if (x_shape <= x2) {
                        // TODO
                    } else if (y_shape <= y2) {
                        // TODO
                    } else if (z_shape <= z2) {
                        // TODO
                    } else {
                        const auto& mesh2 = get_block_mesh2(section_buffer[x2 * x_span + y2 * z_shape + z2]);
                        if (mesh2.transparency == Amulet::BlockMeshTransparency::FullOpaque) {
                            return;
                        }
                    }

                    add_part(*part);
                };

                const auto& parts = mesh.parts;
                if (parts[Amulet::BlockMeshCullDirection::BlockMeshCullNone]) {
                    add_part(*parts[Amulet::BlockMeshCullDirection::BlockMeshCullNone]);
                }
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullUp], 0, 1, 0);
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullDown], 0, -1, 0);
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullNorth], 0, 0, -1);
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullSouth], 0, 0, 1);
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullEast], 1, 0, 0);
                add_part_conditional(parts[Amulet::BlockMeshCullDirection::BlockMeshCullWest], -1, 0, 0);
            }
        }
    }
}

void create_lod0_chunk(
    const std::int64_t cx,
    const std::int64_t cz,
    const Amulet::SectionArrayMap& sections,
    const Amulet::BlockPalette& palette,
    std::string& opaque_buffer,
    std::string& translucent_buffer,
    std::function<const Amulet::BlockMesh(const Amulet::BlockStack&)> get_block_mesh,
    std::function<const std::tuple<float, float, float, float>(const std::string&)> get_texture_bounds)
{
    // Release the GIL so this can run in parallel.
    //py::gil_scoped_release release;

    for (const auto& section : sections.get_arrays()) {
        create_lod0_subchunk(cx, section.first, cz, *section.second, palette, opaque_buffer, translucent_buffer, get_block_mesh, get_texture_bounds);
    }
}

PYBIND11_MODULE(_chunk_mesher_lod0, m)
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

            auto get_block_mesh = [&](const Amulet::BlockStack& block_stack) -> const Amulet::BlockMesh {
                // This bit needs python
                py::gil_scoped_acquire lock;
                py::object py_model = resource_pack.attr("get_block_model")(block_stack);
                return py_model.cast<const Amulet::BlockMesh>();
            };

            auto get_texture_bounds = [&](const std::string& path) -> const std::tuple<float, float, float, float> {
                // This bit needs python
                py::gil_scoped_acquire lock;
                return resource_pack.attr("texture_bounds")(path).cast<std::tuple<float, float, float, float>>();
            };

            create_lod0_chunk(cx, cz, sections, palette, opaque_buffer, translucent_buffer, get_block_mesh, get_texture_bounds);
            return std::make_pair(py::bytes(opaque_buffer), py::bytes(translucent_buffer));
        });
}
