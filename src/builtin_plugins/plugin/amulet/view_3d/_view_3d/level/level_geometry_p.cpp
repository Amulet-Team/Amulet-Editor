#define QT_NO_SIGNALS_SLOTS_KEYWORDS

#include <algorithm>
#include <functional>
#include <list>
#include <mutex>

#include <QCoreApplication>
#include <QOpenGLFunctions>
#include <QThread>
#include <QThreadPool>
#include <QTimer>

#include <amulet/utils/logging.hpp>

#include "chunk_finder.hpp"
#include "chunk_geometry.hpp"
#include "level_geometry.hpp"
#include "level_geometry_p.hpp"
#include "mesh_chunk.hpp"

namespace Amulet {

LevelGeometryGLData::LevelGeometryGLData(QOpenGLContext* context)
    : context(context)
    , matrix_location(0)
{
    surface.create();
}

static const size_t MaxThreadCount = std::max(1, std::min(QThread::idealThreadCount() - 1, 4));
static const size_t ChunkRestartCount = 16;

LevelGeometryImp::LevelGeometryImp(std::shared_ptr<Level> level)
    : _level(std::move(level))
{
    _worker_thread_pool.setMaxThreadCount(MaxThreadCount);
    // QObject::connect(this, &LevelGeometryImp::_mesh_ready, this, &LevelGeometryImp::_init_chunks_gl);
}

void LevelGeometryImp::init_gl()
{
    debug("LevelGeometry::initializeGL()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::init_gl must be called from main thread.");
    }

    QOpenGLContext* context = QOpenGLContext::currentContext();

    std::lock_guard state_lock(_state_mutex);

    if (!_is_destroyed()) {
        throw std::runtime_error("init_gl can only be called from the stopped state.");
    }

    _level_gl_data = std::make_unique<LevelGeometryGLData>(context);

    // Initialise the shader
    auto& program = _level_gl_data->program;
    program.addShaderFromSourceCode(
        QOpenGLShader::ShaderTypeBit::Vertex,
        R"(#version 150
        in vec3 position;
        in vec2 vTexCoord;
        in vec4 vTexOffset;
        in vec3 vTint;

        out vec2 fTexCoord;
        out vec4 fTexOffset;
        out vec3 fTint;

        uniform mat4 transformation_matrix;

        void main() {
            gl_Position = transformation_matrix * vec4(position, 1.0);
            fTexCoord = vTexCoord;
            fTexOffset = vTexOffset;
            fTint = vTint;
        })");

    program.addShaderFromSourceCode(
        QOpenGLShader::ShaderTypeBit::Fragment,
        R"(#version 150
        in vec2 fTexCoord;
        in vec4 fTexOffset;
        in vec3 fTint;

        out vec4 outColor;

        uniform sampler2D image;

        void main(){
            vec4 texColor = texture(
                image,
                vec2(
                    mix(fTexOffset.x, fTexOffset.z, mod(fTexCoord.x, 1.0)),
                    mix(fTexOffset.y, fTexOffset.w, mod(fTexCoord.y, 1.0))
                )
            );
            if(texColor.a < 0.02)
                discard;
            texColor.xyz = texColor.xyz * fTint * 0.85;
            outColor = texColor;
        })");

    program.bindAttributeLocation("position", 0);
    program.bindAttributeLocation("vTexCoord", 1);
    program.bindAttributeLocation("vTexOffset", 2);
    program.bindAttributeLocation("vTint", 3);
    program.link();
    program.bind();
    _level_gl_data->matrix_location = program.uniformLocation("transformation_matrix");
    // Init the texture location
    auto texture_location = program.uniformLocation("image");
    program.setUniformValue(texture_location, 0);
    program.release();

    debug("LevelGeometry::initializeGL() end");
}

bool LevelGeometryImp::_is_awake()
{
    return _manager_thread && _level_gl_data;
}

bool LevelGeometryImp::_is_sleeping()
{
    return !_manager_thread && _level_gl_data;
}

bool LevelGeometryImp::_is_destroyed()
{
    return !_manager_thread && !_level_gl_data;
}

void LevelGeometryImp::wake()
{
    debug("LevelGeometry::wake()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::wake must be called from main thread.");
    }
    std::lock_guard lock(_state_mutex);
    if (!_is_sleeping()) {
        throw std::runtime_error("LevelGeometry can only be woken from the sleeping state.");
    }
    debug("starting manager thread");
    _manager_thread = std::unique_ptr<QThread>(
        QThread::create([this]() { _manager(); }));
    _manager_thread->start(QThread::Priority::IdlePriority);
    debug("LevelGeometry::wake() end");
}

void LevelGeometryImp::sleep()
{
    debug("LevelGeometry::sleep()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::sleep must be called from main thread.");
    }
    debug("LevelGeometry::sleep waiting for lock");
    std::lock_guard lock(_state_mutex);
    debug("LevelGeometry::sleep acquired lock");
    if (!_is_awake()) {
        throw std::runtime_error("LevelGeometry can only be slept from the awake state.");
    }

    debug("Waiting for LevelGeometry::_manager to shut down.");
    // Set the interruption flag.
    _manager_thread->requestInterruption();
    // Wake the manager thread if it is sleeping.
    _wake_chunk_manager();
    // Wait for the thread to finish.
    _manager_thread->wait();
    _manager_thread = nullptr;
    debug("LevelGeometry::_manager has shut down.");

    debug("LevelGeometry::sleep() end");
}

void LevelGeometryImp::destroy_gl()
{
    debug("LevelGeometry::destroy_gl()");
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::destroy_gl must be called from main thread.");
    }
    std::lock_guard lock(_state_mutex);
    if (!_is_sleeping()) {
        throw std::runtime_error("LevelGeometry can only be destroyed from the sleeping state.");
    }

    debug("LevelGeometry: Waiting for thread pool to finish.");
    // Cancel all pending chunk meshing jobs.
    _worker_thread_pool.clear();
    // Wait for running chunk meshing to finish.
    _worker_thread_pool.waitForDone();
    debug("LevelGeometry: Thread pool has finished.");

    {
        // Clear all GPU data.
        std::lock_guard data_lock(_data_mutex);
        _clear_chunks();
        // Destroy the OpenGL data.
        _level_gl_data = nullptr;
    }

    debug("LevelGeometry::destroy_gl() end");
}

LevelGeometryImp::~LevelGeometryImp()
{
    std::lock_guard lock(_state_mutex);
    if (_manager_thread || _level_gl_data) {
        critical("LevelGeometry::destroy_gl must be called before LevelGeometryImp::~LevelGeometryImp.");
        std::terminate();
    }
}

void LevelGeometryImp::paint_gl(QMatrix4x4& projection_matrix, QMatrix4x4& view_matrix)
{
    std::lock_guard state_lock(_state_mutex);
    std::lock_guard data_lock(_data_mutex);
    if (!_level_gl_data || !_gl_texture) {
        return;
    }

    if (QOpenGLContext::currentContext() != _level_gl_data->context) {
        throw std::runtime_error("Context is different.");
    }

    auto* f = QOpenGLContext::currentContext()->functions();

    // Set OpenGL attributes.
    f->glEnable(GL_DEPTH_TEST);
    f->glDepthFunc(GL_LEQUAL);
    f->glEnable(GL_BLEND);
    f->glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    f->glEnable(GL_CULL_FACE);
    f->glCullFace(GL_BACK);

    // Compute the transform
    QMatrix4x4 transform = projection_matrix * view_matrix;

    // Bind the shader program
    auto& program = _level_gl_data->program;
    program.bind();
    auto& matrix_location = _level_gl_data->matrix_location;

    _gl_texture->bind(0);
    for (auto& [_, chunk_geometry] : _level_gl_data->chunks) {
        auto& geometry = chunk_geometry->geometry;
        if (geometry) {
            program.setUniformValue(
                matrix_location,
                transform * chunk_geometry->model_transform);
            geometry->vao.bind();
            f->glDrawArrays(GL_TRIANGLES, 0, geometry->vertex_count);
            geometry->vao.release();
        }
    }

    _gl_texture->release();
    program.release();
}

void LevelGeometryImp::set_resource_pack(std::shared_ptr<AbstractOpenGLResourcePack> gl_resource_pack)
{
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::set_resource_pack must be called from main thread.");
    }
    {
        std::lock_guard lock(_data_mutex);
        if (!_level_gl_data) {
            // This can only run if the opengl state has been initialised
            return;
        }
        _clear_chunks();
        _reset_chunk_finder();
        _gl_resource_pack = std::move(gl_resource_pack);
        _gl_texture = _gl_resource_pack->get_texture_ptr();
    }
    _wake_chunk_manager();
}

void LevelGeometryImp::set_dimension(DimensionId dimension)
{
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::set_dimension must be called from main thread.");
    }
    std::lock_guard lock(_data_mutex);
    if (_dimension != dimension) {
        _dimension = dimension;
        _clear_chunks();
        _reset_chunk_finder();
    }
}

void LevelGeometryImp::set_location(std::int64_t cx, std::int64_t cz)
{
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::set_dimension must be called from main thread.");
    }
    std::lock_guard lock(_data_mutex);
    if (_cx != cx || _cz != cz) {
        // Set the new location
        _cx = cx;
        _cz = cz;

        // Clear chunks outside the unload distance
        _clear_far_chunks();

        if (3 < std::abs(_chunk_finder.cx - _cx) + std::abs(_chunk_finder.cz - _cz)) {
            // If we moved more than 3 chunks, restart the chunk finder immediately.
            _reset_chunk_finder();
        } else {
            // If we are within 3 chunks of the chunk find origin queue restarting.
            _queue_reset_chunk_finder();
        }

        // Resort the chunks with the new coordinate.
        _sort_chunks();
    }
}

void LevelGeometryImp::set_render_distance(std::int64_t load_radius, std::int64_t unload_radius)
{
    if (!QThread::isMainThread()) {
        throw std::runtime_error("LevelGeometry::set_dimension must be called from main thread.");
    }
    std::lock_guard lock(_data_mutex);
    if (unload_radius < _unload_radius) {
        // Clear far chunks if the render distance decreased.
        _unload_radius = unload_radius;
        _clear_far_chunks();
    } else {
        _unload_radius = unload_radius;
    }
    if (load_radius != _load_radius) {
        // Reset the chunk finder if the load distance changed.
        _load_radius = load_radius;
        _reset_chunk_finder();
    } else {
        _load_radius = load_radius;
    }
}

void LevelGeometryImp::_clear_chunks()
{
    debug("LevelGeometry::_clear_chunks()");
    if (!_level_gl_data) {
        return;
    }

    if (!_level_gl_data->context->makeCurrent(&_level_gl_data->surface)) {
        throw std::runtime_error("Could not make context current.");
    }
    // unload the OpenGL data.
    for (auto& [_, chunk_geometry] : _level_gl_data->chunks) {
        // chunk.changed.disconnect(self._reset_chunk_finder)
        if (chunk_geometry->geometry) {
            chunk_geometry->geometry->vao.destroy();
            chunk_geometry->geometry->vbo.destroy();
        }
    }
    _level_gl_data->chunks.clear();
    _level_gl_data->context->doneCurrent();
    debug("LevelGeometry::_clear_chunks() end");
}

void LevelGeometryImp::_clear_far_chunks()
{
    debug("LevelGeometry::_clear_far_chunks()");
    if (!_level_gl_data) {
        return;
    }
    if (_unload_radius == -1) {
        // Not initialised yet.
        return;
    }

    if (!_level_gl_data->context->makeCurrent(&_level_gl_data->surface)) {
        throw std::runtime_error("Could not make context current.");
    }
    // unload the OpenGL data.
    auto& chunks = _level_gl_data->chunks;
    for (auto it = chunks.begin(); it != chunks.end(); /*increment at end*/) {
        auto& [chunk_key, chunk_geometry] = *it;
        auto& [dimension, cx, cz] = chunk_key;
        std::int64_t distance = std::max(
            abs(_cx - cx),
            abs(_cz - cz));
        if (_unload_radius <= distance || _dimension != dimension) {
            // Unload the chunk
            // chunk_data.changed.disconnect(self._reset_chunk_finder)
            if (chunk_geometry->geometry) {
                chunk_geometry->geometry->vao.destroy();
                chunk_geometry->geometry->vbo.destroy();
            }
            it = chunks.erase(it);
        } else {
            it++;
        }
    }
    _level_gl_data->context->doneCurrent();
}

void LevelGeometryImp::_reset_chunk_finder()
{
    debug("LevelGeometry::_reset_chunk_finder()");
    _chunk_finder_needs_reset = false;
    _chunk_finder = { _dimension, _cx, _cz, _load_radius };
    _wake_chunk_manager();
    debug("LevelGeometry::_reset_chunk_finder() end");
}

void LevelGeometryImp::_queue_reset_chunk_finder()
{
    _chunk_finder_needs_reset = true;
    _wake_chunk_manager();
}

void LevelGeometryImp::_sort_chunks() { }

void LevelGeometryImp::_wake_chunk_manager()
{
    _condition.notify_one();
}

void LevelGeometryImp::_manager()
{
    debug("LevelGeometry::_manager()");
    std::unique_lock data_lock(_data_mutex);
    if (!_is_awake()) {
        critical("LevelGeometry should be awake here.");
        return;
    }

    while (
        !_gl_texture && !QThread::currentThread()->isInterruptionRequested()) {
        // Wait until the texture is initialised or interruption is requested.
        _condition.wait(data_lock);
    }

    // The number of chunks we have processed.
    // After ChunkRestartCount processed chunks, the finder should be restarted.
    // This gives a balance between prioritising near chunks and not constantly rebuilding the same chunk.
    size_t processed_count = 0;
    // Loop until thread interruption is requested.
    while (!QThread::currentThread()->isInterruptionRequested()) {
        if (_worker_thread_pool.maxThreadCount() <= _worker_count) {
            debug("hit max thread count. Sleeping");
            // All the threads in the pool are running. Sleep until woken.
            _condition.wait(data_lock);
            continue;
        }

        // Find the next chunk to process.
        std::optional<std::tuple<DimensionId, int, int>> chunk_key;
        std::shared_ptr<ChunkGeometry> chunk_geometry;
        while (true) {
            // Find one chunk to mesh.
            chunk_key = _chunk_finder.next();
            if (chunk_key) {
                auto it = _level_gl_data->chunks.find(*chunk_key);
                if (it == _level_gl_data->chunks.end()) {
                    // has not been generated yet
                    chunk_geometry = nullptr;
                    break;
                }
                chunk_geometry = it->second;
                if (chunk_geometry->processing) {
                    // Skip if the chunk is being meshed.
                    continue;
                }
                if (chunk_geometry->has_changed()) {
                    // has changed since it was last generated
                    break;
                }
            } else {
                break;
            }
        }

        if (!chunk_key) {
            // Reached the end of the iterator
            if (_chunk_finder_needs_reset) {
                _reset_chunk_finder();
                continue;
            }
            // There are no more chunks to process. Sleep until woken.
            _condition.wait(data_lock);
            continue;
        }

        auto& [dimension, cx, cz] = *chunk_key;

        // Create the chunk data object if it doesn't exist.
        if (!chunk_geometry) {
            QMatrix4x4 transform;
            transform.translate(cx * 16, 0, cz * 16);
            auto chunk_handle = _level->get_dimension(dimension)->get_chunk_handle(cx, cz);
            chunk_data = std::make_shared<ChunkGeometry>(std::move(chunk_handle), transform);
            // chunk_data.changed.connect(_reset_chunk_finder);
            _level_gl_data->chunks.emplace(*chunk_key, chunk_geometry);
        }

        // Keep track of which chunks are processing
        chunk_geometry->processing = true;
        // Increment the worker count
        _worker_count += 1;
        // Add the chunk meshing job.
        _worker_thread_pool.start([this, dimension, cx, cz, chunk_geometry]() {
            _worker(dimension, cx, cz, std::move(chunk_geometry));
        });

        processed_count += 1;
        if (ChunkRestartCount <= processed_count && _chunk_finder_needs_reset) {
            // Once we have generated ChunkRestartCount chunks, recheck the nearer chunks.
            processed_count = 0;
            _reset_chunk_finder();
        }
    }
    debug("LevelGeometry::_manager() end");
}

void LevelGeometryImp::_worker(
    DimensionId dimension,
    std::int64_t cx,
    std::int64_t cz,
    std::shared_ptr<ChunkGeometry> chunk_geometry)
{
    // debug(f"Meshing chunk {chunk_key}.");

    // Get the chunk state before we start meshing
    auto chunk_state = chunk_geometry->get_chunk_state();

    // Create a local reference to the resource pack.
    // _gl_resource_pack can get swapped while we are meshing.
    std::shared_ptr<AbstractOpenGLResourcePack> resource_pack;
    {
        std::lock_guard lock(_data_mutex);
        resource_pack = _gl_resource_pack;
    }

    // Do the chunk meshing
    auto [buffer, vertex_count] = mesh_chunk(
        *_level, *resource_pack, dimension, cx, cz);

    // queue OpenGL data creation on the main thread.
    // debug(f"Mesh generated for {chunk_key}");
    {
        std::lock_guard lock(_data_mutex);
        _processed_chunks.emplace_back(
            std::move(dimension),
            cx,
            cz,
            std::move(chunk_geometry),
            chunk_state,
            std::move(buffer),
            vertex_count);
        if (_processed_chunks.size() == 1) {
            // If it is more than 1 there should be an event pending.
            QTimer* timer = new QTimer();
            timer->moveToThread(QCoreApplication::instance()->thread());
            timer->setSingleShot(true);
            QObject::connect(timer, &QTimer::timeout, [this, timer]() {
                // main thread
                _init_chunks_gl();
                timer->deleteLater();
            });
            QMetaObject::invokeMethod(timer, "start", Qt::QueuedConnection, Q_ARG(int, 0));
        }
        _worker_count -= 1;
    }

    // Wake up the manager thread to submit new jobs.
    _wake_chunk_manager();
    // debug(f"Finished meshing chunk {chunk_key}.");
}

void LevelGeometryImp::_init_chunks_gl()
{
    debug("LevelGeometry::_init_chunks_gl()");
    {
        std::lock_guard lock(_data_mutex);
        if (!_level_gl_data || _processed_chunks.empty()) {
            // If the opengl data has been destroyed or there are no processed chunks
            return;
        }
        if (!_level_gl_data->context->makeCurrent(&_level_gl_data->surface)) {
            throw std::runtime_error("Could not make context current.");
        }
        auto* f = QOpenGLContext::currentContext()->functions();
        for (auto& d : _processed_chunks) {
            auto it = _level_gl_data->chunks.find(std::make_tuple(d.dimension, d.cx, d.cz));
            if (it == _level_gl_data->chunks.end() || d.chunk_geometry != it->second) {
                // The chunk data was removed during meshing.
                // This could be because we changed dimension or moved away from the chunk.
                // In these cases just discard the mesh.
                return;
            }

            auto geometry = std::make_unique<ChunkGLData>();
            geometry->vertex_count = d.vertex_count;
            auto& vao = geometry->vao;
            auto& vbo = geometry->vbo;

            // Create the VAO.
            vao.create();
            vao.bind();

            // Create and associate the vbo with the vao
            vbo.create();
            vbo.bind();
            vbo.allocate(d.buffer.c_str(), d.buffer.size());

            // vertex coord
            f->glEnableVertexAttribArray(0);
            f->glVertexAttribPointer(
                0, 3, GL_FLOAT, GL_FALSE, 12 * sizeof(float), 0);
            // texture coord
            f->glEnableVertexAttribArray(1);
            f->glVertexAttribPointer(
                1, 2, GL_FLOAT, GL_FALSE, 12 * sizeof(float), (void*)(3 * sizeof(float)));
            // texture bounds
            f->glEnableVertexAttribArray(2);
            f->glVertexAttribPointer(
                2, 4, GL_FLOAT, GL_FALSE, 12 * sizeof(float), (void*)(5 * sizeof(float)));
            // tint
            f->glEnableVertexAttribArray(3);
            f->glVertexAttribPointer(
                3, 3, GL_FLOAT, GL_FALSE, 12 * sizeof(float), (void*)(9 * sizeof(float)));

            vao.release();
            vbo.release();

            // Update the chunk geometry
            auto old_geometry = d.chunk_geometry->set_geometry(d.chunk_state, std::move(geometry));
            if (old_geometry) {
                // destroy the old data.
                old_geometry->vao.destroy();
                old_geometry->vbo.destroy();
                old_geometry = nullptr;
            }

            // Mark the processing as finished.
            d.chunk_geometry->processing = false;
        }
        _level_gl_data->context->doneCurrent();
        _processed_chunks.clear();
    }
    _wake_chunk_manager();

    geometry_changed.dispatch();
    debug("LevelGeometry::_init_chunks_gl() end");
}

} // namespace Amulet
