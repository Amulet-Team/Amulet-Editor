from typing import Any, TypeVar, Callable, TypeAlias
from collections.abc import Iterator, MutableMapping
import logging
from bisect import bisect_left
from threading import Lock, RLock, Condition
import traceback
import ctypes

from shiboken6 import VoidPtr, getCppPointer, wrapInstance
from PySide6.QtCore import QObject, Signal, QThreadPool, QThread, Qt
from PySide6.QtGui import (
    QMatrix4x4,
    QOpenGLContext,
    QOffscreenSurface,
    QOpenGLFunctions,
)
from PySide6.QtOpenGL import (
    QOpenGLShaderProgram,
    QOpenGLShader,
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLTexture,
)

from OpenGL.constant import IntConstant
from OpenGL.GL import (
    GL_FLOAT as _GL_FLOAT,
    GL_FALSE as _GL_FALSE,
    GL_TRIANGLES as _GL_TRIANGLES,
    GL_CULL_FACE as _GL_CULL_FACE,
    GL_BACK as _GL_BACK,
    GL_DEPTH_TEST as _GL_DEPTH_TEST,
    GL_LEQUAL as _GL_LEQUAL,
    GL_BLEND as _GL_BLEND,
    GL_SRC_ALPHA as _GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA as _GL_ONE_MINUS_SRC_ALPHA,
)

from amulet.utils.cast import dynamic_cast
from amulet.level.abc.dimension import DimensionId
from amulet.level.abc import Level

from amulet.app.exception import (
    CatchExceptionDialog,
    display_exception,
)
from ._settings import render_settings
from ._chunk_mesher import mesh_chunk
from ._resource_pack import (
    OpenGLResourcePack,
    OpenGLResourcePackHandle,
    get_gl_resource_pack_container,
)
from ._chunk_geometry import ChunkData, ChunkGLData

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)

ChunkKey: TypeAlias = tuple[DimensionId, int, int]

T = TypeVar("T")


# This should really be typed better in PyOpenGL
GL_FLOAT = dynamic_cast(_GL_FLOAT, IntConstant)
GL_FALSE = dynamic_cast(_GL_FALSE, IntConstant)
GL_TRIANGLES = dynamic_cast(_GL_TRIANGLES, IntConstant)
GL_CULL_FACE = dynamic_cast(_GL_CULL_FACE, IntConstant)
GL_BACK = dynamic_cast(_GL_BACK, IntConstant)
GL_DEPTH_TEST = dynamic_cast(_GL_DEPTH_TEST, IntConstant)
GL_LEQUAL = dynamic_cast(_GL_LEQUAL, IntConstant)
GL_BLEND = dynamic_cast(_GL_BLEND, IntConstant)
GL_SRC_ALPHA = dynamic_cast(_GL_SRC_ALPHA, IntConstant)
GL_ONE_MINUS_SRC_ALPHA = dynamic_cast(_GL_ONE_MINUS_SRC_ALPHA, IntConstant)


class Thread(QThread):
    def __init__(self, function: Callable[[], None]) -> None:
        super().__init__()
        self.function = function

    def run(self) -> None:
        self.function()


class ChunkContainer(MutableMapping[ChunkKey, ChunkData]):
    """A container which orders chunks based on distance from the camera."""

    def __init__(self) -> None:
        self._chunks: dict[ChunkKey, ChunkData] = {}
        self._order: list[ChunkKey] = []
        self._x: int = 0
        self._z: int = 0

    def __hash__(self) -> int:
        return id(self)

    def set_position(self, cx: int, cz: int) -> None:
        self._x = cx
        self._z = cz
        self._order = sorted(self._order, key=self._dist)

    def __contains__(self, k: ChunkKey | Any) -> bool:
        return k in self._chunks

    def _dist(self, k: ChunkKey) -> int:
        return -abs(k[1] - self._x) - abs(k[2] - self._z)

    def __setitem__(self, k: ChunkKey, v: ChunkData) -> None:
        if k not in self._chunks:
            self._order.insert(
                bisect_left(self._order, self._dist(k), key=self._dist), k
            )
        self._chunks[k] = v

    def __delitem__(self, v: ChunkKey) -> None:
        del self._chunks[v]
        self._order.remove(v)

    def __getitem__(self, k: ChunkKey) -> ChunkData:
        return self._chunks[k]

    def __len__(self) -> int:
        return len(self._chunks)

    def __iter__(self) -> Iterator[ChunkKey]:
        yield from self._order

    def clear(self) -> None:
        self._chunks.clear()
        self._order.clear()


def empty_iterator() -> Iterator[ChunkKey]:
    yield from ()


def get_grid_spiral(
    dimension: DimensionId, cx: int, cz: int, radius: int
) -> Iterator[ChunkKey]:
    """A generator that yields a 2D grid spiraling from the centre."""
    sign = 1
    length = 1
    for _ in range(radius * 2 + 1):
        for _ in range(length):
            yield dimension, cx, cz
            cx += sign
        for _ in range(length):
            yield dimension, cx, cz
            cz += sign
        sign *= -1
        length += 1


class ProcessedChunkData:
    chunk_key: ChunkKey
    chunk_data: ChunkData
    chunk_state: int
    buffer: bytes
    vertex_count: int

    def __init__(
        self,
        chunk_key: ChunkKey,
        chunk_data: ChunkData,
        chunk_state: int,
        buffer: bytes,
        vertex_count: int,
    ) -> None:
        self.chunk_key = chunk_key
        self.chunk_data = chunk_data
        self.chunk_state = chunk_state
        self.buffer = buffer
        self.vertex_count = vertex_count


class LevelGeometryGLData:
    """
    All data that only exists after OpenGL initialisation.
    This is grouped together so there is only one "is not None" check.
    """

    # Immutable data
    context: QOpenGLContext
    context_ptr: int
    program: QOpenGLShaderProgram
    matrix_location: int

    # Mutable data. All read and writes must be done with the lock.
    # Storage for data related to each chunk.
    chunks: ChunkContainer
    # Chunks that have been processed but need initialising in OpenGL.
    processed_chunks: list[ProcessedChunkData]

    def __init__(
        self,
        context: QOpenGLContext,
        program: QOpenGLShaderProgram,
        matrix_location: int,
    ):
        self.context = context
        self.context_ptr = getCppPointer(context)[0]
        self.program = program
        self.matrix_location = matrix_location
        self.chunks = ChunkContainer()
        self.processed_chunks = []

    def __del__(self) -> None:
        log.debug("LevelGeometryGLData.__del__")


MaxThreadCount = max(1, min(QThread.idealThreadCount() - 1, 4))
ChunkRestartCount = 16


class LevelGeometry(QObject):
    """
    A class to render a level.
    This must exist on the main thread.
    """

    _level: Level
    _dimension: DimensionId | None
    _camera_chunk: tuple[int, int] | None
    _chunk_finder: Iterator[ChunkKey]

    # OpenGL attributes
    _gl_lock: Lock
    # Constant OpenGL attributes
    _gl_resource_pack_handle: OpenGLResourcePackHandle
    _surface: QOffscreenSurface
    # Mutable OpenGL Attributes
    # _gl_lock must be held when accessing/setting these variables.
    # The objects must be destroyed by the main thread.
    # The main thread may hold onto them in local variables.
    _gl_resource_pack: OpenGLResourcePack | None
    _gl_texture: QOpenGLTexture | None
    _level_gl_data: LevelGeometryGLData | None

    # Threads
    # A condition for the manager thread to wait on.
    _lock: RLock
    _condition: Condition
    # The thread dispatching jobs
    _manager_thread: None | QThread
    # The pool of threads processing the meshes.
    _worker_thread_pool: QThreadPool
    _worker_count: int

    _new_processed_chunks = Signal()
    # The geometry has changed and needs repainting.
    geometry_changed = Signal()

    def __init__(self, level: Level) -> None:
        log.debug("LevelGeometry.__init__()")
        if not QThread.isMainThread():
            raise RuntimeError("LevelGeometry must be constructed by the main thread.")

        super().__init__()
        self._level = level
        self._dimension = None
        self._camera_chunk = None
        self._chunk_finder = empty_iterator()

        self._gl_lock = Lock()
        self._gl_resource_pack_handle = get_gl_resource_pack_container(level)
        self._gl_resource_pack = None
        self._gl_texture = None
        self._level_gl_data = None
        # Used to modify the OpenGL data.
        # The owner surface may have been destroyed in some cases.
        self._surface = QOffscreenSurface()
        self._surface.create()

        self._lock = RLock()
        self._condition = Condition(self._lock)
        self._manager_thread = None

        self._worker_thread_pool: QThreadPool = QThreadPool()
        self._worker_thread_pool.setThreadPriority(QThread.Priority.IdlePriority)
        self._worker_thread_pool.setMaxThreadCount(MaxThreadCount)
        self._worker_count = 0

        self._new_processed_chunks.connect(
            self._init_chunks_gl, Qt.ConnectionType.QueuedConnection
        )

        log.debug("LevelGeometry.__init__() end")

    def init_gl(self) -> None:
        """
        Initialise the OpenGL data.
        Must be called once by the main thread with a valid OpenGL context enabled.
        This context must be active for all calls that need one.
        """
        log.debug("LevelGeometry.initializeGL()")
        if not QThread.isMainThread():
            raise RuntimeError("LevelGeometry.init_gl must be called from main thread.")

        context = QOpenGLContext.currentContext()
        # if not QOpenGLContext.areSharing(context, QOpenGLContext.globalShareContext()):
        #     raise RuntimeError(
        #         "The widget context is not sharing with the global context."
        #     )

        if self._level_gl_data is not None:
            raise RuntimeError("gl_data is not None.")

        # Initialise the shader
        program = QOpenGLShaderProgram()
        program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex,
            """#version 150
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
            }""",
        )

        program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment,
            """#version 150
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
            }""",
        )

        program.bindAttributeLocation("position", 0)
        program.bindAttributeLocation("vTexCoord", 1)
        program.bindAttributeLocation("vTexOffset", 2)
        program.bindAttributeLocation("vTint", 3)
        program.link()
        program.bind()
        matrix_location = program.uniformLocation("transformation_matrix")
        # Init the texture location
        texture_location = program.uniformLocation("image")
        program.setUniformValue1i(texture_location, 0)
        program.release()

        self._level_gl_data = LevelGeometryGLData(context, program, matrix_location)
        log.debug("LevelGeometry.initializeGL() end")

    def start(self) -> None:
        """
        Start background processing.
        This must be called by the main thread.
        Call this on canvas.showEvent
        """
        log.debug("LevelGeometry.start()")
        if not QThread.isMainThread():
            raise RuntimeError("LevelGeometry.start must be called from main thread.")

        render_settings.render_distance_changed.connect(self._on_render_distance_change)
        self._gl_resource_pack_handle.changed.connect(self._set_resource_pack)

        # Create and start the manager thread.
        if self._manager_thread is None:
            self._manager_thread = Thread(self._chunk_manager)
            self._manager_thread.start(QThread.Priority.IdlePriority)
        log.debug("LevelGeometry.start() end")

    def stop(self) -> None:
        """
        Stops background processing.
        If any chunks are still processing they will finish.
        This must be called by the main thread.
        Call this on canvas.hideEvent
        """
        log.debug("LevelGeometry.stop()")
        if not QThread.isMainThread():
            raise RuntimeError("LevelGeometry.stop must be called from main thread.")

        render_settings.render_distance_changed.disconnect(
            self._on_render_distance_change
        )
        self._gl_resource_pack_handle.changed.disconnect(self._set_resource_pack)

        if self._manager_thread is not None:
            # Set the interruption flag.
            self._manager_thread.requestInterruption()
            # Wake the manager thread if it is sleeping.
            self._wake_chunk_manager()
            # Wait for the thread to finish.
            self._manager_thread.wait()
            self._manager_thread = None
        # Note that we allow the thread pool to continue.
        # This will be called when the editor is minimised and the currently processing chunks can continue
        log.debug("LevelGeometry.stop() end")

    def destroy_gl(self) -> None:
        """
        Destroy the OpenGL data.
        This must be called by the main thread.
        This must be called by the context.aboutToBeDestroyed signal.
        """
        log.debug("LevelGeometry.destroy_gl()")
        if not QThread.isMainThread():
            raise RuntimeError(
                "LevelGeometry.destroy_gl must be called from main thread."
            )
        gl_data = self._level_gl_data
        if gl_data is None:
            raise RuntimeError("gl_data is None.")
        log.debug("LevelGeometry: Waiting for thread pool to finish.")
        # Cancel all pending chunk meshing jobs.
        self._worker_thread_pool.clear()
        # Wait for running chunk meshing to finish.
        self._worker_thread_pool.waitForDone()
        log.debug("LevelGeometry: Thread pool has finished.")
        # The C++ object still exists at this point but the link to the Python object has been broken.
        # We can create a new Python object wrapping the C++ object and use it until it is actually destroyed.
        gl_data.context = dynamic_cast(
            wrapInstance(gl_data.context_ptr, QOpenGLContext), QOpenGLContext
        )
        self._clear_chunks()
        self._level_gl_data = None
        log.debug("LevelGeometry.destroy_gl() end")

    def __del__(self) -> None:
        log.debug("LevelGeometry.__del__()")

    def paint_gl(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        """
        Draw the level.
        This must be called by the main thread with the context active.

        :param projection_matrix: The camera internal projection matrix.
        :param view_matrix: The camera external matrix.
        """
        with self._gl_lock:
            gl_data = self._level_gl_data
            texture = self._gl_texture
            if gl_data is None or texture is None:
                return

        if QOpenGLContext.currentContext() is not gl_data.context:
            raise RuntimeError("Context is different.")

        f = QOpenGLContext.currentContext().functions()

        # Set OpenGL attributes.
        f.glEnable(GL_DEPTH_TEST)
        f.glDepthFunc(GL_LEQUAL)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        f.glEnable(GL_CULL_FACE)
        f.glCullFace(GL_BACK)

        # Bind the shader program
        program = gl_data.program
        program.bind()

        transform = projection_matrix * view_matrix
        # Lock so that other threads can't write to chunks
        with self._lock:
            texture.bind(0)
            for chunk_data in gl_data.chunks.values():
                geometry = chunk_data.geometry
                if geometry is None:
                    continue
                program.setUniformValue(
                    gl_data.matrix_location, transform * chunk_data.model_transform
                )
                geometry.vao.bind()
                f.glDrawArrays(GL_TRIANGLES, 0, geometry.vertex_count)
                geometry.vao.release()

        program.release()

    def set_dimension(self, dimension: DimensionId) -> None:
        """
        Set the active dimension.
        This must be called by the main thread.
        """
        log.debug("LevelGeometry.set_dimension()")
        if not QThread.isMainThread():
            raise RuntimeError(
                "LevelGeometry.set_dimension must be called from main thread."
            )
        with self._lock:
            if dimension != self._dimension:
                self._dimension = dimension
                self._clear_chunks()
                self._reset_chunk_finder()

    def set_location(self, cx: int, cz: int) -> None:
        """
        Set the chunk the camera is in.
        This must be called by the main thread.
        """
        log.debug("LevelGeometry.set_location()")
        if not QThread.isMainThread():
            raise RuntimeError(
                "LevelGeometry.set_location must be called from main thread."
            )
        location = (cx, cz)
        with self._lock:
            if location != self._camera_chunk:
                self._camera_chunk = location
                self._clear_far_chunks()
                self._reset_chunk_finder()
                if self._level_gl_data is not None:
                    self._level_gl_data.chunks.set_position(cx, cz)

    def _on_render_distance_change(self) -> None:
        log.debug("LevelGeometry._on_render_distance_change()")
        with self._lock:
            self._clear_far_chunks()
            self._reset_chunk_finder()

    def _set_resource_pack(self, gl_resource_pack: OpenGLResourcePack) -> None:
        log.debug("LevelGeometry._set_resource_pack()")
        with self._lock:
            # Mark all existing chunks as changed
            if self._level_gl_data is None:
                # This can only run if the opengl state has been initialised
                return
            self._clear_chunks()
            self._reset_chunk_finder()
            with self._gl_lock:
                self._gl_resource_pack = gl_resource_pack
                self._gl_texture = self._gl_resource_pack.get_texture()
            # The chunk manager may be waiting for the resource pack.
            self._wake_chunk_manager()

    def _clear_chunks(self) -> None:
        """
        Destroy all chunk data.
        This must be called by the main thread.
        """
        log.debug("LevelGeometry._clear_chunks()")
        if not QThread.isMainThread():
            raise RuntimeError("_clear_chunks can only be called from main thread.")

        with self._lock:
            gl_data = self._level_gl_data
            if gl_data is None:
                return

            if not gl_data.context.makeCurrent(self._surface):
                raise RuntimeError("Could not make context current.")
            # unload the OpenGL data.
            for chunk in gl_data.chunks.values():
                chunk.changed.disconnect(self._reset_chunk_finder)
                geometry = chunk.geometry
                if geometry is not None:
                    geometry.vao.destroy()
                    geometry.vbo.destroy()
            gl_data.chunks.clear()
            gl_data.context.doneCurrent()

    def _clear_far_chunks(self) -> None:
        """
        Unload all chunk data outside the unload render distance.
        This must be called by the main thread.
        """
        log.debug("LevelGeometry._clear_far_chunks()")
        if not QThread.isMainThread():
            raise RuntimeError(
                "LevelGeometry._clear_far_chunks must be called from main thread."
            )
        with self._lock:
            gl_data = self._level_gl_data
            if gl_data is None:
                return

            if self._camera_chunk is None:
                return
            camera_dimension = self._dimension
            camera_cx, camera_cz = self._camera_chunk

            unload_distance = render_settings.chunk_unload_distance

            if not gl_data.context.makeCurrent(self._surface):
                raise RuntimeError("Could not make context current.")
            # unload the OpenGL data.
            safe_chunks: dict[ChunkKey, ChunkData] = {}
            for chunk_key, chunk_data in gl_data.chunks.items():
                dimension_id, cx, cz = chunk_key
                distance = max(
                    abs(camera_cx - cx),
                    abs(camera_cz - cz),
                )
                if unload_distance <= distance or camera_dimension != dimension_id:
                    # Unload the chunk
                    chunk_data.changed.disconnect(self._reset_chunk_finder)
                    geometry = chunk_data.geometry
                    if geometry is not None:
                        geometry.vao.destroy()
                        geometry.vbo.destroy()
                else:
                    # Store it to be re-added
                    safe_chunks[chunk_key] = chunk_data

            gl_data.chunks.clear()
            gl_data.chunks.update(safe_chunks)
            gl_data.context.doneCurrent()

    def _reset_chunk_finder(self) -> None:
        log.debug("LevelGeometry._reset_chunk_finder()")
        with self._lock:
            if self._dimension is None or self._camera_chunk is None:
                self._chunk_finder = empty_iterator()
            else:
                cx, cz = self._camera_chunk
                self._chunk_finder = get_grid_spiral(
                    self._dimension, cx, cz, render_settings.chunk_load_distance
                )
                self._wake_chunk_manager()

    def _wake_chunk_manager(self) -> None:
        """
        Wake up the chunk thread if it is sleeping.
        Thread safe.
        """
        log.debug("LevelGeometry._wake_chunk_manager()")
        with self._lock:
            self._condition.notify()

    def _chunk_manager(self) -> None:
        """
        Submit chunks for meshing.
        This must be thread safe.
        """
        with (
            CatchExceptionDialog("Error in chunk manager thread.", suppress=False),
            self._lock,
        ):
            gl_data = self._level_gl_data
            if gl_data is None:
                raise RuntimeError("gl_data must not be None here.")

            while (
                not QThread.currentThread().isInterruptionRequested()
                and self._gl_texture is None
            ):
                # Sleep until the resource pack is loaded
                self._condition.wait()

            # The number of chunks we have processed.
            # After ChunkRestartCount processed chunks, the finder should be restarted.
            # This gives a balance between prioritising near chunks and not constantly rebuilding the same chunk.
            processed_count = 0
            # Loop until thread interruption is requested.
            while not QThread.currentThread().isInterruptionRequested():
                if self._worker_thread_pool.maxThreadCount() <= self._worker_count:
                    log.debug("hit max thread count. Sleeping")
                    # All the threads in the pool are running. Sleep until woken.
                    self._condition.wait()
                    continue

                # Find the next chunk to process.
                chunk_key: ChunkKey | None
                chunk_data: ChunkData | None = None
                while True:
                    try:
                        # Find one chunk to mesh.
                        chunk_key = next(self._chunk_finder)
                    except StopIteration:
                        # If no chunk is found
                        chunk_key = None
                        break
                    else:
                        chunk_data = gl_data.chunks.get(chunk_key)
                        if chunk_data is None:
                            # has not been generated yet
                            break
                        if chunk_data.processing:
                            # Skip if the chunk is being meshed.
                            continue
                        if chunk_data.has_changed():
                            # has changed since it was last generated
                            break

                if chunk_key is None:
                    # There are no more chunks to process. Sleep until woken.
                    self._condition.wait()
                    continue

                # Create the chunk data object if it doesn't exist.
                if chunk_data is None:
                    dimension, cx, cz = chunk_key
                    transform = QMatrix4x4()
                    transform.translate(cx * 16, 0, cz * 16)
                    chunk_handle = self._level.get_dimension(
                        dimension
                    ).get_chunk_handle(cx, cz)
                    chunk_data = ChunkData(
                        chunk_handle,
                        transform,
                    )
                    chunk_data.changed.connect(self._reset_chunk_finder)
                    gl_data.chunks[chunk_key] = chunk_data

                # Keep track of which chunks are processing
                chunk_data.processing = True
                # Increment the worker count
                self._worker_count += 1
                # Add the chunk meshing job.
                self._start_chunk_mesher(chunk_key, gl_data, chunk_data)

                processed_count += 1
                if ChunkRestartCount <= processed_count:
                    # Once we have generated ChunkRestartCount chunks, recheck the nearer chunks.
                    processed_count = 0
                    self._reset_chunk_finder()
        log.debug("LevelGeometry._chunk_manager() end")

    def _start_chunk_mesher(
        self,
        chunk_key: ChunkKey,
        level_gl_data: LevelGeometryGLData,
        chunk_data: ChunkData,
    ) -> None:
        """Needed so that the variables in the lambda don't change."""
        self._worker_thread_pool.start(
            lambda: self._chunk_mesher(chunk_key, level_gl_data, chunk_data)
        )

    def _chunk_mesher(
        self,
        chunk_key: ChunkKey,
        level_gl_data: LevelGeometryGLData,
        chunk_data: ChunkData,
    ) -> None:
        """
        The chunk mesher function submitted by :meth:`_queue_chunks`
        This must be thread safe.
        """
        log.debug(f"Meshing chunk {chunk_key}.")
        try:
            chunk_state = chunk_data.chunk_state
            resource_pack = self._gl_resource_pack
            if resource_pack is None:
                raise RuntimeError("resource pack has not been initialised")

            # Do the chunk meshing
            dimension, cx, cz = chunk_key
            buffer, vertex_count = mesh_chunk(
                self._level, resource_pack, dimension, cx, cz
            )

        except Exception as e:
            with self._lock:
                # Remove the chunk key from the processing set.
                chunk_data.processing = False
            display_exception(
                f"Error meshing chunk {chunk_key}.",
                error=str(e),
                traceback=traceback.format_exc(),
            )
        else:
            # queue OpenGL data creation on the main thread.
            log.debug(f"Mesh generated for {chunk_key}")
            with self._lock:
                level_gl_data.processed_chunks.append(
                    ProcessedChunkData(
                        chunk_key,
                        chunk_data,
                        chunk_state,
                        buffer,
                        vertex_count,
                    )
                )
                if len(level_gl_data.processed_chunks) == 1:
                    # If it is more than 1 there should be an event pending.
                    self._new_processed_chunks.emit()
        with self._lock:
            self._worker_count -= 1
        # Wake up the manager thread to submit new jobs.
        self._wake_chunk_manager()
        log.debug(f"Finished meshing chunk {chunk_key}.")

    def _init_chunks_gl(self) -> None:
        """
        Initialise the OpenGL state for the chunks.
        This must be called on the main thread
        """
        log.debug("LevelGeometry._init_chunks_gl()")
        with self._lock, CatchExceptionDialog("LevelGeometry._init_chunks_gl"):
            level_gl_data = self._level_gl_data
            if level_gl_data is None or not level_gl_data.processed_chunks:
                # If the opengl data has been destroyed or there are no processed chunks
                return
            if not level_gl_data.context.makeCurrent(self._surface):
                raise RuntimeError("Could not make context current.")
            f = QOpenGLContext.currentContext().functions()
            for processed_chunk_data in level_gl_data.processed_chunks:
                chunk_key = processed_chunk_data.chunk_key
                chunk_data = processed_chunk_data.chunk_data
                chunk_state = processed_chunk_data.chunk_state
                buffer = processed_chunk_data.buffer
                vertex_count = processed_chunk_data.vertex_count
                try:
                    log.debug(f"Creating OpenGL data for chunk {chunk_key}")
                    if level_gl_data.chunks.get(chunk_key) is not chunk_data:
                        # The chunk data was removed during meshing.
                        # This could be because we changed dimension or moved away from the chunk.
                        # In these cases just discard the mesh.
                        return

                    # Create the VAO.
                    vao = QOpenGLVertexArrayObject()
                    vao.create()
                    vao.bind()

                    # Create and associate the vbo with the vao
                    vbo = QOpenGLBuffer()
                    vbo.create()
                    vbo.bind()
                    vbo.allocate(buffer, len(buffer))

                    # vertex coord
                    f.glEnableVertexAttribArray(0)
                    f.glVertexAttribPointer(
                        0, 3, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(0)
                    )
                    # texture coord
                    f.glEnableVertexAttribArray(1)
                    f.glVertexAttribPointer(
                        1, 2, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(3 * FloatSize)
                    )
                    # texture bounds
                    f.glEnableVertexAttribArray(2)
                    f.glVertexAttribPointer(
                        2, 4, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(5 * FloatSize)
                    )
                    # tint
                    f.glEnableVertexAttribArray(3)
                    f.glVertexAttribPointer(
                        3, 3, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(9 * FloatSize)
                    )

                    vao.release()
                    vbo.release()

                    geometry = ChunkGLData(
                        vbo,
                        vertex_count,
                        vao,
                    )
                    # Update the chunk geometry
                    old_geometry = chunk_data.set_geometry(chunk_state, geometry)
                    if old_geometry is not None:
                        # destroy the old data.
                        old_geometry.vao.destroy()
                        old_geometry.vbo.destroy()
                except Exception as e:
                    display_exception(
                        f"Error creating OpenGL data for chunk {chunk_key}.",
                        error=str(e),
                        traceback=traceback.format_exc(),
                    )
                else:
                    log.debug(f"Finished creating OpenGL data for chunk {chunk_key}")
                finally:
                    # Remove the chunk key from the processing set.
                    chunk_data.processing = False
            level_gl_data.context.doneCurrent()
            level_gl_data.processed_chunks.clear()
            self._wake_chunk_manager()
            self.geometry_changed.emit()
