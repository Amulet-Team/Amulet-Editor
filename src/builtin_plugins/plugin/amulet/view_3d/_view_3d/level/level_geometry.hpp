#pragma once

#include <memory>
#include <mutex>

#include <QMatrix4x4>

#include <amulet/level/abc/dimension.hpp>
#include <amulet/level/abc/level.hpp>

#include <amulet/utils/event.hpp>

#include <_view_3d/resource_pack/abc.hpp>

namespace Amulet {

class LevelGeometryImp;

class LevelGeometry {
private:
    LevelGeometryImp* _impl;

public:
    LevelGeometry(std::shared_ptr<Level>);
    ~LevelGeometry();

    LevelGeometry(const LevelGeometry&) = delete;
    LevelGeometry(LevelGeometry&&) = delete;
    LevelGeometry& operator=(const LevelGeometry&) = delete;
    LevelGeometry& operator=(LevelGeometry&&) = delete;

    // The following must be called in this order
    // init_gl > wake <=> sleep > destroy_gl

    // Initialise the OpenGL data.
    // Must be called once by the main thread with a valid OpenGL context enabled.
    // This context must be active for all calls that need one.
    void init_gl();

    // Wake from the sleeping state.
    // This must be called by the main thread.
    // Call this on canvas.showEvent
    void wake();

    // Stops background processing.
    // If any chunks are still processing they will finish.
    // This must be called by the main thread.
    // Call this on canvas.hideEvent
    void sleep();

    // Destroy the OpenGL data.
    // This must be called by the main thread.
    // This must be called before the destruction of the context.
    void destroy_gl();

    // Draw the level.
    // This must be called by the main thread with the context active.
    void paint_gl(QMatrix4x4& projection_matrix, QMatrix4x4& view_matrix);

    // Set the resource pack the level uses.
    void set_resource_pack(std::shared_ptr<AbstractOpenGLResourcePack>);

    // Set the dimension being displayed.
    // This must be called by the main thread.
    void set_dimension(DimensionId dimension);

    // Set the chunk the camera is in.
    // This must be called by the main thread.
    void set_location(std::int64_t cx, std::int64_t cz);

    // Set the render distances.
    // This must be called by the main thread.
    void set_render_distance(std::int64_t load_radius, std::int64_t unload_radius);

    Event<>& get_geometry_changed();
};

} // namespace Amulet
