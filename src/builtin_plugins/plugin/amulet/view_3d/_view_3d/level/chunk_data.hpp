#pragma once

#include <memory>
#include <mutex>

#include <amulet/utils/event.hpp>

#include <amulet/level/abc/chunk_handle.hpp>

#include <QMatrix4x4>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>

namespace Amulet {

struct ChunkGLData {
    QOpenGLBuffer vbo;
    size_t vertex_count;
    QOpenGLVertexArrayObject vao;
};

class ChunkData {
private:
    std::mutex _mutex;

public:
    // Constant data
    // The chunk handle.Used to get notified when the chunk changed.
    std::shared_ptr<ChunkHandle> chunk_handle;
    // The world transform
    QMatrix4x4 model_transform;
    // The token the chunk changed event
    EventToken<> changed_token;

    // The OpenGL data.
    // This will get incremented each time the chunk is changed.
    size_t chunk_state;
    // If chunk and mesh tokens are the same then the mesher does not need to be run.
    size_t geometry_state;
    // None if geometry has not been generated or ChunkGLData if it has.
    std::unique_ptr<ChunkGLData> geometry;

    // Is this geometry being processed.
    bool processing;

    Event<> changed;

    ChunkData(std::shared_ptr<ChunkHandle>, QMatrix4x4& transform);

    ~ChunkData();

    bool has_changed();

    void mark_changed();

    std::unique_ptr<ChunkGLData> set_geometry(
        size_t geometry_state,
        std::unique_ptr<ChunkGLData> geometry);
};

} // namespace Amulet
