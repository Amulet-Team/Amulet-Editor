#include <functional>
#include <list>
#include <mutex>

#include <QMatrix4x4>
#include <QOffscreenSurface>
#include <QOpenGLContext>
#include <QOpenGLShaderProgram>
#include <QOpenGLTexture>
#include <QThreadPool>

#include <amulet/level/abc/level.hpp>
#include <amulet/utils/logging.hpp>

#include "chunk_finder.hpp"
#include "chunk_geometry.hpp"
#include "level_geometry.hpp"
#include <_view_3d/resource_pack/abc.hpp>

namespace Amulet {

struct ProcessedChunkData {
    DimensionId dimension;
    std::int64_t cx;
    std::int64_t cz;
    std::shared_ptr<ChunkGeometry> chunk_geometry;
    size_t chunk_state;
    std::string opaque_buffer;
    size_t opaque_vertex_count;
    std::string translucent_buffer;
    size_t translucent_vertex_count;
};

class LevelGeometryGLData {
public:
    QOpenGLContext* context;
    QOffscreenSurface surface;
    QOpenGLShaderProgram program;
    int matrix_location;
    std::map<std::tuple<DimensionId, int, int>, std::shared_ptr<ChunkGeometry>> chunks;
    std::list<std::shared_ptr<ChunkGeometry>> sorted_chunks;

    LevelGeometryGLData(QOpenGLContext*);
};

class LevelGeometryImp {

public:
    LevelGeometryImp(std::shared_ptr<Level>);
    ~LevelGeometryImp();

    LevelGeometryImp(const LevelGeometryImp&) = delete;
    LevelGeometryImp(LevelGeometryImp&&) = delete;
    LevelGeometryImp& operator=(const LevelGeometryImp&) = delete;
    LevelGeometryImp& operator=(LevelGeometryImp&&) = delete;

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

    Event<> geometry_changed;

private:
    // Threading stuff
    std::mutex _state_mutex; // _manager_thread and _level_gl_data
    std::unique_ptr<QThread> _manager_thread;
    QThreadPool _worker_thread_pool;

    // Mutex for all other data
    std::mutex _data_mutex;
    std::condition_variable _condition;

    size_t _worker_count = 0;

    // OpenGL data
    std::unique_ptr<LevelGeometryGLData> _level_gl_data;
    std::shared_ptr<AbstractOpenGLResourcePack> _gl_resource_pack;
    QOpenGLTexture* _gl_texture = nullptr;

    // Data for chunks that have been meshed but not uploaded to the GPU.
    std::list<ProcessedChunkData> _processed_chunks;

    // The level object
    std::shared_ptr<Level> _level;

    // The camera position
    DimensionId _dimension = "";
    std::int64_t _cx = 0;
    std::int64_t _cz = 0;

    // Render distance
    std::int64_t _load_radius = -1;
    std::int64_t _unload_radius = -1;

    // Track if the chunk finder should be reset.
    bool _chunk_finder_needs_reset = false;
    // Iterator of chunk coords to process
    ChunkFinder _chunk_finder = { "", 0, 0, -1 };

    bool _is_awake();
    bool _is_sleeping();
    bool _is_destroyed();

    // Destroy GL data for the chunk and disconnect events.
    // This must be called before deleting the ChunkGeometry object.
    // This must be called on the main thread with the context active.
    void _destroy_chunk_geometry(ChunkGeometry&);

    // Destroy all chunk data.
    // Must be called on the main thread.
    // Must be called with the mutex locked.
    void _clear_chunks();

    // Destroy all chunk data outside the unload distance.
    // Must be called on the main thread.
    // Must be called with the mutex locked.
    void _clear_far_chunks();

    // Reset the chunk coordinate finder
    // Must be called with the mutex locked.
    void _reset_chunk_finder();

    // Queue the resetting of the chunk finder
    void _queue_reset_chunk_finder();

    // Sort chunk geometry based on distance from the camera.
    void _sort_chunks();

    // Wake up the chunk manager.
    // Thread safe.
    // Lock does not need to be held.
    void _wake_chunk_manager();

    // The manager job
    void _manager();

    // The worker job
    void _worker(
        DimensionId dimension,
        std::int64_t cx,
        std::int64_t cz,
        std::shared_ptr<ChunkGeometry>);

    // Push the processed chunk meshes to the GPU
    // This must be called on the main thread.
    void _init_chunks_gl();
};

} // namespace Amulet
