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

    // Function to get the block mesh.
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

    // Get array shape info
    const auto& sections = *all_chunk_data[2]->get_sections();
    const auto& section_shape = sections.get_array_shape();
    const std::int32_t x_shape = std::get<0>(section_shape);
    const std::int32_t y_shape = std::get<1>(section_shape);
    const std::int32_t z_shape = std::get<2>(section_shape);
    const auto x_stride = y_shape * z_shape;
    const auto y_stride = z_shape;

    const auto& block_arrays = sections.get_arrays();
    // For each section in the chunk.
    for (const auto& it : block_arrays) {
        const std::int64_t& cy = it.first;
        const IndexArray3D& section = *it.second;
        
        const auto& section_buffer = section.get_buffer();

        // Make a transparency 3D array two elements larger than one section in each direction
        const std::int32_t padded_x_shape = x_shape + 2;
        const std::int32_t padded_y_shape = y_shape + 2;
        const std::int32_t padded_z_shape = z_shape + 2;
        const auto padded_x_stride = padded_y_shape * padded_z_shape;
        const auto padded_y_stride = padded_z_shape;
        std::vector<BlockMeshTransparency> transparency_array(
            padded_x_shape * padded_y_shape * padded_z_shape,
            BlockMeshTransparency::Partial
        );

        // Populate the transparency array with values from the block models.
        for (std::int32_t x = 0; x < x_shape; x++) {
            for (std::int32_t y = 0; y < y_shape; y++) {
                for (std::int32_t z = 0; z < z_shape; z++) {
                    const auto& block_id = section_buffer[x * x_stride + y * y_stride + z];
                    const auto& mesh = get_block_mesh(0, 0, block_id);
                    transparency_array[(x + 1) * padded_x_stride + (y + 1) * padded_y_stride + z + 1] = mesh.transparency;
                }
            }
        }

        // Up
        auto up_it = block_arrays.find(cy + 1);
        if (up_it != block_arrays.end()) {
            const auto& up_buffer = up_it->second->get_buffer();
            for (std::int32_t x = 0; x < x_shape; x++) {
                for (std::int32_t z = 0; z < z_shape; z++) {
                    const auto& block_id = up_buffer[x * x_stride + 0 * y_stride + z];
                    const auto& mesh = get_block_mesh(0, 0, block_id);
                    transparency_array[(x + 1) * padded_x_stride + (padded_y_shape - 1) * padded_y_stride + z + 1] = mesh.transparency;
                }
            }
        }

        // Down
        auto down_it = block_arrays.find(cy - 1);
        if (down_it != block_arrays.end()) {
            const auto& up_buffer = down_it->second->get_buffer();
            for (std::int32_t x = 0; x < x_shape; x++) {
                for (std::int32_t z = 0; z < z_shape; z++) {
                    const auto& block_id = up_buffer[x * x_stride + (y_shape - 1) * y_stride + z];
                    const auto& mesh = get_block_mesh(0, 0, block_id);
                    transparency_array[(x + 1) * padded_x_stride + 0 * padded_y_stride + z + 1] = mesh.transparency;
                }
            }
        }
        
        // North
        if (all_chunk_data[0]) {
            const auto& neighbour_block_component = *all_chunk_data[0];
            const auto& neighbour_sections = *neighbour_block_component.get_sections();
            if (neighbour_sections.get_array_shape() != section_shape) {
                throw std::invalid_argument("North section shape does not match.");
            }
            const auto& neighbour_block_arrays = neighbour_sections.get_arrays();
            auto it = neighbour_block_arrays.find(cy);
            if (it != neighbour_block_arrays.end()) {
                const auto& arr = it->second->get_buffer();
                const auto& palette = neighbour_block_component.get_palette();
                for (std::int32_t x = 0; x < x_shape; x++) {
                    for (std::int32_t y = 0; y < y_shape; y++) {
                        const auto& block_id = arr[x * x_stride + y * y_stride + (z_shape - 1)];
                        const auto& mesh = get_block_mesh(0, -1, block_id);
                        transparency_array[(x + 1) * padded_x_stride + (y + 1) * padded_y_stride + 0] = mesh.transparency;
                    }
                }
            }
        }

        // West
        if (all_chunk_data[3]) {
            const auto& neighbour_block_component = *all_chunk_data[3];
            const auto& neighbour_sections = *neighbour_block_component.get_sections();
            if (neighbour_sections.get_array_shape() != section_shape) {
                throw std::invalid_argument("East section shape does not match.");
            }
            const auto& neighbour_block_arrays = neighbour_sections.get_arrays();
            auto it = neighbour_block_arrays.find(cy);
            if (it != neighbour_block_arrays.end()) {
                const auto& arr = it->second->get_buffer();
                const auto& palette = neighbour_block_component.get_palette();
                for (std::int32_t y = 0; y < y_shape; y++) {
                    for (std::int32_t z = 0; z < z_shape; z++) {
                        const auto& block_id = arr[0 * x_stride + y * y_stride + z];
                        const auto& mesh = get_block_mesh(1, 0, block_id);
                        transparency_array[(padded_x_shape - 1) * padded_x_stride + (y + 1) * padded_y_stride + z + 1] = mesh.transparency;
                    }
                }
            }
        }

        // South
        if (all_chunk_data[4]) {
            const auto& neighbour_block_component = *all_chunk_data[4];
            const auto& neighbour_sections = *neighbour_block_component.get_sections();
            if (neighbour_sections.get_array_shape() != section_shape) {
                throw std::invalid_argument("South section shape does not match.");
            }
            const auto& neighbour_block_arrays = neighbour_sections.get_arrays();
            auto it = neighbour_block_arrays.find(cy);
            if (it != neighbour_block_arrays.end()) {
                const auto& arr = it->second->get_buffer();
                const auto& palette = neighbour_block_component.get_palette();
                for (std::int32_t x = 0; x < x_shape; x++) {
                    for (std::int32_t y = 0; y < y_shape; y++) {
                        const auto& block_id = arr[x * x_stride + y * y_stride + 0];
                        const auto& mesh = get_block_mesh(0, 1, block_id);
                        transparency_array[(x + 1) * padded_x_stride + (y + 1) * padded_y_stride + padded_z_shape - 1] = mesh.transparency;
                    }
                }
            }
        }

        // West
        if (all_chunk_data[1]) {
            const auto& neighbour_block_component = *all_chunk_data[1];
            const auto& neighbour_sections = *neighbour_block_component.get_sections();
            if (neighbour_sections.get_array_shape() != section_shape) {
                throw std::invalid_argument("West section shape does not match.");
            }
            const auto& neighbour_block_arrays = neighbour_sections.get_arrays();
            auto it = neighbour_block_arrays.find(cy);
            if (it != neighbour_block_arrays.end()) {
                const auto& arr = it->second->get_buffer();
                const auto& palette = neighbour_block_component.get_palette();
                for (std::int32_t y = 0; y < y_shape; y++) {
                    for (std::int32_t z = 0; z < z_shape; z++) {
                        const auto& block_id = arr[(x_shape - 1) * x_stride + y * y_stride + z];
                        const auto& mesh = get_block_mesh(-1, 0, block_id);
                        transparency_array[0 * padded_x_stride + (y + 1) * padded_y_stride + z + 1] = mesh.transparency;
                    }
                }
            }
        }

        for (std::int32_t x = 0; x < x_shape; x++) {
            for (std::int32_t y = 0; y < y_shape; y++) {
                for (std::int32_t z = 0; z < z_shape; z++) {
                    const auto& block_id = section_buffer[x * x_stride + y * y_stride + z];
                    const auto& mesh = get_block_mesh(0, 0, block_id);

                    auto& buffer = mesh.transparency == BlockMeshTransparency::FullOpaque ? opaque_buffer : translucent_buffer;

                    auto add_part = [&](const BlockMeshPart& part, float shading) {
                        auto add_vert = [&](size_t index, const std::tuple<float, float, float, float>& bounds) {
                            const auto& vert = part.verts[index];
                            size_t buffer_size = buffer.size();
                            buffer.resize(buffer_size + sizeof(float) * 12);
                            float* float_arr = reinterpret_cast<float*>(&buffer[buffer_size]);
                            float_arr[0] = vert.coord.x + x;
                            float_arr[1] = cy * y_shape + y + vert.coord.y;
                            float_arr[2] = vert.coord.z + z;
                            float_arr[3] = vert.texture_coord.x;
                            float_arr[4] = vert.texture_coord.y;
                            float_arr[5] = std::get<0>(bounds);
                            float_arr[6] = std::get<1>(bounds);
                            float_arr[7] = std::get<2>(bounds);
                            float_arr[8] = std::get<3>(bounds);
                            float_arr[9] = vert.tint.x * shading;
                            float_arr[10] = vert.tint.y * shading;
                            float_arr[11] = vert.tint.z * shading;
                            };
                        for (const auto& triangle : part.triangles) {
                            const auto& bounds = resource_pack.texture_bounds(mesh.textures[triangle.texture_index]);
                            add_vert(triangle.vert_index_a, bounds);
                            add_vert(triangle.vert_index_b, bounds);
                            add_vert(triangle.vert_index_c, bounds);
                        }
                        };

                    auto add_part_conditional = [&](
                        const std::optional<BlockMeshPart>& part, 
                        std::int32_t dx, 
                        std::int32_t dy, 
                        std::int32_t dz,
                        float shading
                    ) {
                        if (!part) {
                            return;
                        }
                        std::int32_t x2 = x + dx + 1;
                        std::int32_t y2 = y + dy + 1;
                        std::int32_t z2 = z + dz + 1;

                        switch (transparency_array[x2 * padded_x_stride + y2 * padded_y_stride + z2]) {
                        case BlockMeshTransparency::FullOpaque:
                            // If neighbour block is full and opque then skip.
                            return;
                        case BlockMeshTransparency::FullTranslucent:
                            if (mesh.transparency == BlockMeshTransparency::FullTranslucent) {
                                // If both blocks are full translucent then skip.
                                return;
                            }
                        }

                        add_part(*part, shading);
                        };

                    const auto& parts = mesh.parts;
                    if (parts[BlockMeshCullDirection::BlockMeshCullNone]) {
                        add_part(*parts[BlockMeshCullDirection::BlockMeshCullNone], 1.0);
                    }
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullUp], 0, 1, 0, 1.0);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullDown], 0, -1, 0, 0.55);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullNorth], 0, 0, -1, 0.85);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullSouth], 0, 0, 1, 0.85);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullEast], 1, 0, 0, 0.7);
                    add_part_conditional(parts[BlockMeshCullDirection::BlockMeshCullWest], -1, 0, 0, 0.7);
                }
            }
        }
    }
}

} // namespace Amulet
