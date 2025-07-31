#pragma once

#include <memory>
#include <mutex>

#include <amulet/utils/event.hpp>

#include <amulet/level/abc/chunk_handle.hpp>

#include <QMatrix4x4>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>

namespace Amulet {

class ChunkHandle;

struct ChunkGLData {
    QOpenGLBuffer vbo;
    size_t vertex_count;
    QOpenGLVertexArrayObject vao;
};

class ChunkGeometry {
public:
    // Constant data
    // The chunk handle.Used to get notified when the chunk changed.
    const std::shared_ptr<ChunkHandle> chunk_handle;
    // The world transform
    const QMatrix4x4 model_transform;
    
    // The OpenGL data.
    // nullptr if geometry has not been generated or ChunkGLData if it has.
    std::unique_ptr<ChunkGLData> geometry;

    // Owner data.
    // Is this geometry being processed.
    bool processing = false;
    // A place for the owner to store a chunk changed token.
    std::unique_ptr<EventToken<>> changed_token;

    ChunkGeometry(std::shared_ptr<ChunkHandle>, QMatrix4x4& transform);

    ~ChunkGeometry();

    bool has_changed();

    size_t get_chunk_state();

    std::unique_ptr<ChunkGLData> set_geometry(
        size_t geometry_state,
        std::unique_ptr<ChunkGLData> geometry);

private:
    std::mutex _mutex;

    // This will get incremented each time the chunk is changed.
    size_t _chunk_state = 1;
    // If chunk and mesh tokens are the same then the mesher does not need to be run.
    size_t _geometry_state = 0;
    
    // The token the chunk changed event
    EventToken<> _changed_token;

    void _mark_changed();
};

} // namespace Amulet
