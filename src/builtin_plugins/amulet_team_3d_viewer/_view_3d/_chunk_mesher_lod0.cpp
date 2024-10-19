#include "_chunk_mesher_lod0.hpp"

namespace Amulet {


void create_lod0_chunk(
    AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz,
    const ChunkData& all_chunk_data,
    std::string& opaque_buffer,
    std::string& translucent_buffer)
{
    // Borrowed pointers to the mesh object or nullptr if not initialised.
    std::array<std::vector<const BlockMesh*>, 5> all_block_meshes;

    // Resize mesh vectors to fit all the blocks in the palette.
    for (size_t i = 0; i < 5; i++) {
        const Amulet::BlockComponentData* block_component = all_chunk_data[i];
        if (block_component) {
            all_block_meshes[i].resize(block_component->get_palette()->size());
        }
    }

    auto get_block_mesh = [&](const std::int8_t dcx, const std::int8_t dcz, const std::uint32_t block_id) -> const BlockMesh& {
        const std::int8_t chunk_index = 2 + dcx + 2 * dcz;
        auto& block_meshes = all_block_meshes[chunk_index];
        const auto* ptr = block_meshes[block_id];
        if (ptr) {
            return *ptr;
        }
        else {
            const auto& chunk_data = all_chunk_data[chunk_index];
            const auto& block_stack = *chunk_data->get_palette()->index_to_block_stack(block_id);
            const BlockMesh* mesh_ptr = &resource_pack.get_block_model(block_stack);
            block_meshes[block_id] = mesh_ptr;
            return *mesh_ptr;
        }
    };

    for (const auto& it : all_chunk_data[2]->get_sections()->get_arrays()) {
        //create_lod0_subchunk(resource_pack, get_block_mesh, cx, section.first, cz, *section.second, palette, opaque_buffer, translucent_buffer);

        const std::int64_t& cy = it.first;
        const IndexArray3D& section = *it.second;
        
        const auto& section_shape = section.get_shape();
        const std::int32_t x_shape = std::get<0>(section_shape);
        const std::int32_t y_shape = std::get<1>(section_shape);
        const std::int32_t z_shape = std::get<2>(section_shape);
        const auto x_span = y_shape * z_shape;
        const auto& section_buffer = section.get_buffer();

        for (std::int32_t x = 0; x < x_shape; x++) {
            for (std::int32_t y = 0; y < y_shape; y++) {
                for (std::int32_t z = 0; z < z_shape; z++) {
                    const auto& block_id = section_buffer[x * x_span + y * z_shape + z];
                    const auto& mesh = get_block_mesh(0, 0, block_id);

                    auto add_part = [&](const BlockMeshPart& part) {
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
                            const auto& bounds = resource_pack.texture_bounds(mesh.textures[triangle.texture_index]);
                            add_vert(triangle.vert_index_a, bounds);
                            add_vert(triangle.vert_index_b, bounds);
                            add_vert(triangle.vert_index_c, bounds);
                        }
                        };

                    auto add_part_conditional = [&](const std::optional<BlockMeshPart>& part, std::int32_t dx, std::int32_t dy, std::int32_t dz) {
                        if (!part) {
                            return;
                        }
                        std::int32_t x2 = x + dx;
                        std::int32_t y2 = y + dy;
                        std::int32_t z2 = z + dz;

                        if (x2 < 0) {
                            // TODO
                        }
                        else if (y2 < 0) {
                            // TODO
                        }
                        else if (z2 < 0) {
                            // TODO
                        }
                        else if (x_shape <= x2) {
                            // TODO
                        }
                        else if (y_shape <= y2) {
                            // TODO
                        }
                        else if (z_shape <= z2) {
                            // TODO
                        }
                        else {
                            const auto& mesh2 = get_block_mesh(0, 0, section_buffer[x2 * x_span + y2 * z_shape + z2]);
                            if (mesh2.transparency == BlockMeshTransparency::FullOpaque) {
                                return;
                            }
                        }

                        add_part(*part);
                        };

                    const auto& parts = mesh.parts;
                    if (parts[BlockMeshCullDirection::BlockMeshCullNone]) {
                        add_part(*parts[BlockMeshCullDirection::BlockMeshCullNone]);
                    }
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullUp], 0, 1, 0);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullDown], 0, -1, 0);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullNorth], 0, 0, -1);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullSouth], 0, 0, 1);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullEast], 1, 0, 0);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullWest], -1, 0, 0);
                }
            }
        }
    }
}

} // namespace Amulet
