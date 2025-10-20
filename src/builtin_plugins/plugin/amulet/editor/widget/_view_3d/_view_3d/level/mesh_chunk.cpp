#include <limits>
#include <memory>
#include <string_view>

#include <amulet/core/chunk/component/block_component.hpp>

#include "mesh_chunk.hpp"

namespace Amulet {

static std::pair<float, float> _get_bounds(
    const std::variant<SelectionBox, SelectionBoxGroup>& bounds)
{
    return std::visit(
        [](auto&& arg) -> std::pair<float, float> {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, SelectionBox>) {
                return { arg.min_y(), arg.max_y() };
            } else {
                static_assert(std::is_same_v<T, SelectionBoxGroup>);
                const auto& boxes = arg.get_boxes();
                if (boxes.empty()) {
                    return { 0, 256 };
                }
                std::int64_t min_y = std::numeric_limits<std::int64_t>::max();
                std::int64_t max_y = std::numeric_limits<std::int64_t>::min();
                for (const auto& box : boxes) {
                    if (box.min_y() < min_y) {
                        min_y = box.min_y();
                    }
                    if (box.max_y() > max_y) {
                        max_y = box.max_y();
                    }
                }
                return { min_y, max_y };
            }
        },
        bounds);
}

static float _get_min_y(
    const std::variant<SelectionBox, SelectionBoxGroup>& bounds)
{
    return std::visit(
        [](auto&& arg) -> float {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, SelectionBox>) {
                return arg.min_y();
            } else {
                static_assert(std::is_same_v<T, SelectionBoxGroup>);
                const auto& boxes = arg.get_boxes();
                if (boxes.empty()) {
                    return 0;
                }
                std::int64_t min_y = std::numeric_limits<std::int64_t>::max();
                for (const auto& box : boxes) {
                    if (box.min_y() < min_y) {
                        min_y = box.min_y();
                    }
                }
                return min_y;
            }
        },
        bounds);
}

static float _get_max_y(
    const std::variant<SelectionBox, SelectionBoxGroup>& bounds)
{
    return std::visit(
        [](auto&& arg) -> float {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, SelectionBox>) {
                return arg.max_y();
            } else {
                static_assert(std::is_same_v<T, SelectionBoxGroup>);
                const auto& boxes = arg.get_boxes();
                if (boxes.empty()) {
                    return 0;
                }
                std::int64_t max_y = std::numeric_limits<std::int64_t>::max();
                for (const auto& box : boxes) {
                    if (box.max_y() < max_y) {
                        max_y = box.max_y();
                    }
                }
                return max_y;
            }
        },
        bounds);
}

// The number of floats in 1 vertex
// (x, y, z, tx, ty, tbound*4, tintr, tintg, tintb)
static const size_t floats_per_vert = 12;
static const size_t tris_per_quad_pair = 4;
static const size_t verts_per_tri = 3;
static const size_t verts_per_quad_pair = tris_per_quad_pair * verts_per_tri;
static const size_t floats_per_quad_pair = verts_per_quad_pair * floats_per_vert;

// Map vertex index to coordinate index.
static const size_t vertex_to_coord[verts_per_quad_pair] = {
    0,
    1,
    2,
    2,
    1,
    3,
    1,
    0,
    3,
    3,
    0,
    2,
};

static const size_t vertex_to_texture_coord[verts_per_quad_pair] = {
    0,
    1,
    2,
    2,
    1,
    3,
    0,
    1,
    2,
    2,
    1,
    3,
};

static void _create_chunk_plane(float* buffer, float height)
{
    // The coordinate of each vertex in the quad
    float coords[4][3] = {
        { 0, height, 0 },
        { 0, height, 16 },
        { 16, height, 0 },
        { 16, height, 16 },
    };

    float texture_coords[4][2] = {
        { 0, 0 },
        { 0, 1 },
        { 1, 0 },
        { 1, 1 },
    };

    //
    for (size_t vertex_index = 0; vertex_index < verts_per_quad_pair; vertex_index++) {
        size_t float_index = vertex_index * floats_per_vert;
        size_t coord_index = vertex_to_coord[vertex_index];
        size_t texture_coord_index = vertex_to_texture_coord[vertex_index];
        buffer[float_index + 0] = coords[coord_index][0];
        buffer[float_index + 1] = coords[coord_index][1];
        buffer[float_index + 2] = coords[coord_index][2];
        buffer[float_index + 3] = texture_coords[texture_coord_index][0];
        buffer[float_index + 4] = texture_coords[texture_coord_index][1];
    }
}

static std::string _create_grid(
    const std::variant<SelectionBox, SelectionBoxGroup>& level_bounds,
    AbstractOpenGLResourcePack& resource_pack,
    const std::string& texture_namespace,
    const std::string& texture_path,
    bool draw_floor,
    bool draw_ceil,
    std::array<float, 3> tint)
{
    // 2 triangles for up and 2 for down
    const size_t quad_pair_count = draw_floor + draw_ceil;
    const size_t float_count = quad_pair_count * floats_per_quad_pair;
    std::string buffer(float_count * sizeof(float), 0);
    float* float_arr = reinterpret_cast<float*>(&buffer[0]);
    if (draw_floor && draw_ceil) {
        auto [min_y, max_y] = _get_bounds(level_bounds);
        _create_chunk_plane(&float_arr[0], min_y - 0.01);
        _create_chunk_plane(&float_arr[floats_per_quad_pair], max_y + 0.01);
    } else if (draw_floor) {
        _create_chunk_plane(&float_arr[0], _get_min_y(level_bounds) - 0.01);
    } else if (draw_ceil) {
        _create_chunk_plane(&float_arr[0], _get_max_y(level_bounds) + 0.01);
    } else {
        return "";
    }

    auto texture_bounds = resource_pack.get_texture_bounds(
        resource_pack.get_texture_path(
            texture_namespace,
            texture_path));
    for (size_t float_index = 0; float_index < float_count; float_index += floats_per_vert) {
        float_arr[float_index + 5] = std::get<0>(texture_bounds);
        float_arr[float_index + 6] = std::get<1>(texture_bounds);
        float_arr[float_index + 7] = std::get<2>(texture_bounds);
        float_arr[float_index + 8] = std::get<3>(texture_bounds);
        float_arr[float_index + 9] = std::get<0>(tint);
        float_arr[float_index + 10] = std::get<1>(tint);
        float_arr[float_index + 11] = std::get<2>(tint);
    }
    return buffer;
}

static std::string _get_empty_geometry(
    const std::variant<SelectionBox, SelectionBoxGroup>& level_bounds,
    AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz)
{
    return _create_grid(
        level_bounds,
        resource_pack,
        "amulet",
        "amulet_ui/chunk_grid_null",
        true,
        true,
        ((cx + cz) % 2 ? std::array<float, 3> { 1.0, 1.0, 1.0 } : std::array<float, 3> { 0.8, 0.8, 0.8 }));
}

static std::string _get_error_geometry(
    std::variant<SelectionBox, SelectionBoxGroup> level_bounds,
    AbstractOpenGLResourcePack& resource_pack,
    const std::int64_t cx,
    const std::int64_t cz)
{
    return _create_grid(
        level_bounds,
        resource_pack,
        "amulet",
        "amulet_ui/chunk_grid_error",
        true,
        true,
        ((cx + cz) % 2 ? std::array<float, 3> { 1.0, 1.0, 1.0 } : std::array<float, 3> { 0.8, 0.8, 0.8 }));
}

static std::shared_ptr<BlockStorage> _get_block_component(
    Dimension& dimension,
    const std::int64_t cx,
    const std::int64_t cz)
{
    std::unique_ptr<Chunk> chunk;
    try {
        chunk = dimension.get_chunk_handle(cx, cz)->get_chunk(std::set<std::string> { BlockComponent::ComponentID });
    } catch (const ChunkLoadError& e) {
        return nullptr;
    }

    auto* block_component = dynamic_cast<BlockComponent*>(chunk.get());
    if (block_component) {
        return block_component->get_block_storage();
    } else {
        return nullptr;
    }
}

std::tuple<std::string, size_t, std::string, size_t> mesh_chunk(
    Level& level,
    AbstractOpenGLResourcePack& resource_pack,
    const DimensionId& dimension_id,
    const std::int64_t cx,
    const std::int64_t cz)
{
    OrderedLockGuard<ThreadAccessMode::Read, ThreadShareMode::SharedReadWrite> lock(level.get_mutex());
    if (!level.is_open()) {
        throw std::runtime_error("The level has been closed.");
    }

    auto dimension = level.get_dimension(dimension_id);

    std::unique_ptr<Chunk> chunk;
    std::string opaque_buffer;
    std::string translucent_buffer;

    try {
        chunk = dimension->get_chunk_handle(cx, cz)->get_chunk(std::set<std::string> { BlockComponent::ComponentID });
    } catch (const ChunkDoesNotExist& e) {
        // log.debug(f"Chunk {dimension_id}, {cx}, {cz} does not exist")
        opaque_buffer = _get_empty_geometry(dimension->get_bounds(), resource_pack, cx, cz);
    } catch (const ChunkLoadError& e) {
        // log.exception(
        //     f"Error loading chunk {dimension_id}, {cx}, {cz}", exc_info=True
        // )
        opaque_buffer = _get_error_geometry(dimension->get_bounds(), resource_pack, cx, cz);
    }

    if (chunk) {
        auto* block_component = dynamic_cast<BlockComponent*>(chunk.get());
        if (block_component) {
            // log.debug(f"Creating geometry for chunk {dimension_id}, {cx}, {cz}")
            auto self = block_component->get_block_storage();
            auto north = _get_block_component(*dimension, cx, cz - 1);
            auto east = _get_block_component(*dimension, cx + 1, cz);
            auto south = _get_block_component(*dimension, cx, cz + 1);
            auto west = _get_block_component(*dimension, cx - 1, cz);
            mesh_chunk_lod0(
                resource_pack,
                cx,
                cz,
                *self,
                north.get(), 
                east.get(), 
                south.get(),
                west.get(), 
                opaque_buffer,
                translucent_buffer);
        } else {
            // log.debug(
            //     f"Chunk {dimension_id}, {cx}, {cz} does not implement BlockComponent."
            // )
        }
    }

    // log.debug(f"Generated array for {dimension_id}, {cx}, {cz}")

    size_t opaque_vertex_count = opaque_buffer.size() / (12 * sizeof(float));
    size_t translucent_vertex_count = translucent_buffer.size() / (12 * sizeof(float));
    // log.debug(f"Generated chunk {dimension_id}, {cx}, {cz}")
    return { opaque_buffer, opaque_vertex_count, translucent_buffer, translucent_vertex_count };
}

} // namespace Amulet
