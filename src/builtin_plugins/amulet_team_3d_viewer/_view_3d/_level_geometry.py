from typing import Any, TypeVar, Callable, TypeAlias
from collections.abc import Iterator, MutableMapping
import logging
from bisect import bisect_left
from threading import Condition, RLock
import traceback
import ctypes

from shiboken6 import VoidPtr
from PySide6.QtCore import QObject, Signal, QThreadPool, QThread
from PySide6.QtGui import QMatrix4x4, QOpenGLContext, QOffscreenSurface
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

from amulet.data_types import DimensionId
from amulet.level.abc import Level

from amulet_editor.models.widgets.traceback_dialog import (
    DisplayException,
    display_exception,
)
from ._settings import render_settings
from ._chunk_mesher import mesh_chunk
from ._resource_pack import OpenGLResourcePack, get_gl_resource_pack_container
from ._chunk_geometry import ChunkData, ChunkGLData

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)

ChunkKey: TypeAlias = tuple[DimensionId, int, int]

T = TypeVar("T")


def dynamic_cast(obj: Any, new_type: type[T]) -> T:
    if not isinstance(obj, new_type):
        raise TypeError(f"{obj} is not an instance of {new_type}")
    return obj


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


class LevelGeometryGLData:
    """
    All data that only exists after OpenGL initialisation.
    This is grouped together so there is only one "is not None" check.
    """

    # Immutable data
    context: QOpenGLContext
    program: QOpenGLShaderProgram
    matrix_location: int

    # Mutable data. All read and writes must be done with the lock.
    # Chunk data.
    chunks: ChunkContainer
    # Chunks that are currently being processed.
    processing_chunks: set[ChunkKey]

    def __init__(
        self,
        context: QOpenGLContext,
        program: QOpenGLShaderProgram,
        matrix_location: int,
    ):
        self.context = context
        self.program = program
        self.matrix_location = matrix_location
        self.chunks = ChunkContainer()
        self.processing_chunks = set()

    def __del__(self) -> None:
        log.debug("LevelGeometryGLData.__del__")


# MaxThreadCount = QThread.idealThreadCount() * 4
MaxThreadCount = 4


class LevelGeometry(QObject):
    """
    A class to render a level.
    This must exist on the main thread.
    """

    _dimension: DimensionId | None
    _camera_chunk: tuple[int, int] | None
    _chunk_finder: Iterator[ChunkKey]

    # OpenGL attributes
    _gl_data: LevelGeometryGLData | None
    _surface: QOffscreenSurface

    # Threads
    # The thread dispatching jobs
    _manager_thread: None | QThread
    # A condition for the manager thread to wait on.
    _manager_condition: Condition
    # The pool of threads processing the meshes.
    _worker_threads: QThreadPool

    # The geometry has changed and needs repainting.
    geometry_changed = Signal()
    # Signal to call OpenGL chunk data initialisation in the main thread.
    _init_chunk_gl_signal = Signal(
        LevelGeometryGLData,
        tuple,  # ChunkKey,
        ChunkData,
        int,
        bytes,
        int,
    )

    def __init__(self, level: Level) -> None:
        log.debug("LevelGeometry.__init__ start")
        super().__init__()
        self._level = level
        self._resource_pack_holder = get_gl_resource_pack_container(level)
        self._resource_pack: OpenGLResourcePack | None = None
        self._texture: QOpenGLTexture | None = None

        self._lock = RLock()
        self._dimension = None
        self._camera_chunk = None
        self._chunk_finder = empty_iterator()

        self._gl_data = None
        # Used to modify the OpenGL data.
        # The owner surface may have been destroyed in some cases.
        self._surface = QOffscreenSurface()
        self._surface.create()

        self._manager_thread = None
        self._manager_condition = Condition(self._lock)

        self._worker_threads: QThreadPool = QThreadPool()
        self._worker_threads.setThreadPriority(QThread.Priority.IdlePriority)
        self._worker_threads.setMaxThreadCount(MaxThreadCount)

        render_settings.render_distance_changed.connect(self._on_render_distance_change)
        self._resource_pack_holder.changed.connect(self._on_resource_pack_change)
        self._init_chunk_gl_signal.connect(self._init_chunk_gl)

    def init_gl(self) -> None:
        """
        Initialise the OpenGL data.
        Must be called once by the main thread with a valid OpenGL context enabled.
        This context must be active for all calls that need one.
        """
        log.debug("LevelGeometry.initializeGL start")
        context = QOpenGLContext.currentContext()
        # if not QOpenGLContext.areSharing(context, QOpenGLContext.globalShareContext()):
        #     raise RuntimeError(
        #         "The widget context is not sharing with the global context."
        #     )

        if self._gl_data is not None:
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

        self._gl_data = LevelGeometryGLData(context, program, matrix_location)
        log.debug("LevelGeometry.initializeGL end")

    def start(self) -> None:
        """
        Start background processing.
        This must be called by the main thread.
        Call this on canvas.showEvent
        """
        # Create and start the manager thread.
        if self._manager_thread is None:
            self._manager_thread = Thread(self._chunk_thread)
            self._manager_thread.start(QThread.Priority.IdlePriority)

    def stop(self) -> None:
        """
        Stops background processing.
        If any chunks are still processing they will finish.
        This must be called by the main thread.
        Call this on canvas.hideEvent
        """
        if self._manager_thread is not None:
            # Set the interruption flag.
            self._manager_thread.requestInterruption()
            # Wake the manager thread if it is sleeping.
            self._wake_chunk_thread()
            # Wait for the thread to finish.
            self._manager_thread.wait()
            self._manager_thread = None

    def destroy_gl(self) -> None:
        """
        Destroy the OpenGL data.
        This must be called by the main thread.
        This must be called by the context.aboutToBeDestroyed signal.
        """
        gl_data = self._gl_data
        if gl_data is None:
            raise RuntimeError("gl_data is None.")
        # Cancel all pending chunk meshing jobs.
        self._worker_threads.clear()
        # Wait for running chunk meshing to finish.
        self._worker_threads.waitForDone()
        self._clear_chunks()
        self._gl_data = None

    def __del__(self) -> None:
        log.debug("SharedLevelGeometry.__del__")

    def paint_gl(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        """
        Draw the level.
        This must be called by the main thread with the context active.

        :param projection_matrix: The camera internal projection matrix.
        :param view_matrix: The camera external matrix.
        """
        gl_data = self._gl_data
        texture = self._texture
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
        if dimension != self._dimension:
            with self._lock:
                self._dimension = dimension
                self._clear_chunks()
                self._reset_chunk_finder()

    def set_location(self, cx: int, cz: int) -> None:
        """
        Set the chunk the camera is in.
        This must be called by the main thread.
        """
        location = (cx, cz)
        if location != self._camera_chunk:
            with self._lock:
                self._camera_chunk = location
                self._clear_far_chunks()
                self._reset_chunk_finder()
                if self._gl_data is not None:
                    self._gl_data.chunks.set_position(cx, cz)

    def _on_render_distance_change(self) -> None:
        with self._lock:
            self._clear_far_chunks()
            self._reset_chunk_finder()

    def _on_resource_pack_change(self) -> None:
        with self._lock:
            # Mark all existing chunks as changed
            gl_data = self._gl_data
            if gl_data is None:
                return
            self._clear_chunks()
            self._reset_chunk_finder()
            self._resource_pack = self._resource_pack_holder.resource_pack
            self._texture = self._resource_pack.get_texture()

    def _clear_chunks(self) -> None:
        """
        Destroy all chunk data.
        This must be called by the main thread.
        """
        gl_data = self._gl_data
        if gl_data is None:
            return

        with self._lock:
            if not gl_data.context.makeCurrent(self._surface):
                raise RuntimeError("Could not make context current.")
            # unload the OpenGL data.
            for chunk in gl_data.chunks.values():
                chunk.chunk_handle.changed.disconnect(self._reset_chunk_finder)
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
        gl_data = self._gl_data
        if gl_data is None:
            return

        if self._camera_chunk is None:
            return
        camera_dimension = self._dimension
        camera_cx, camera_cz = self._camera_chunk

        unload_distance = render_settings.chunk_unload_distance

        with self._lock:
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
                    chunk_data.chunk_handle.changed.disconnect(self._reset_chunk_finder)
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
        if self._dimension is None or self._camera_chunk is None:
            self._chunk_finder = empty_iterator()
        else:
            cx, cz = self._camera_chunk
            self._chunk_finder = get_grid_spiral(
                self._dimension, cx, cz, render_settings.chunk_load_distance
            )
            self._wake_chunk_thread()

    def _wake_chunk_thread(self) -> None:
        """
        Wake up the chunk thread if it is sleeping.
        Thread safe.
        """
        with self._lock:
            self._manager_condition.notify()

    def _chunk_thread(self) -> None:
        """
        Submit chunks for meshing.
        This must be thread safe.
        """
        with DisplayException("Error in chunk manager thread."):
            gl_data = self._gl_data
            if gl_data is None:
                raise RuntimeError("gl_data must not be None here.")

            # The resource pack may initially be None. Wait until it is loaded.
            with self._lock:
                while (
                    not QThread.currentThread().isInterruptionRequested()
                    and not self._resource_pack_holder.loaded
                ):
                    self._manager_condition.wait()

            # The number of chunks we have processed.
            # After MaxThreadCount processed chunks, the finder should be restarted.
            # This gives a balance between prioritising near chunks and not constantly rebuilding the same chunk.
            processed_count = 0
            # Loop until thread interruption is requested.
            while not QThread.currentThread().isInterruptionRequested():
                with self._lock:
                    if (
                        self._worker_threads.maxThreadCount()
                        <= self._worker_threads.activeThreadCount()
                    ):
                        # All the threads in the pool are running. Sleep until woken.
                        self._manager_condition.wait()
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
                            if chunk_key in gl_data.processing_chunks:
                                # If the chunk is being meshed then skip.
                                continue
                            chunk_data = gl_data.chunks.get(chunk_key)
                            if chunk_data is None or chunk_data.has_changed():
                                # has not been generated yet or has changed since it was last generated
                                break

                    if chunk_key is None:
                        # There are no more chunks to process. Sleep until woken.
                        self._manager_condition.wait()
                        continue

                    # Keep track of which chunks are processing
                    gl_data.processing_chunks.add(chunk_key)
                    # Create the chunk data object if it doesn't exist.
                    if chunk_data is None:
                        dimension, cx, cz = chunk_key
                        transform = QMatrix4x4()
                        transform.translate(cx * 16, 0, cz * 16)
                        chunk_data = ChunkData(
                            self._level.get_dimension(dimension).get_chunk_handle(
                                cx, cz
                            ),
                            transform,
                        )
                        chunk_data.chunk_handle.changed.connect(
                            self._reset_chunk_finder
                        )
                        gl_data.chunks[chunk_key] = chunk_data
                    # Add the chunk meshing job.
                    self._start_chunk_mesher(chunk_key, gl_data, chunk_data)

                    processed_count += 1
                    if MaxThreadCount <= processed_count:
                        # Once we have generated MaxThreadCount chunks, recheck the nearer chunks.
                        processed_count = 0
                        self._reset_chunk_finder()

    def _start_chunk_mesher(
        self,
        chunk_key: ChunkKey,
        level_gl_data: LevelGeometryGLData,
        chunk_data: ChunkData,
    ) -> None:
        """Needed so that the variables in the lambda don't change."""
        self._worker_threads.start(
            lambda: self._chunk_mesher(chunk_key, level_gl_data, chunk_data)
        )

    def _finish_chunk_mesher(
        self, level_gl_data: LevelGeometryGLData, chunk_key: ChunkKey
    ) -> None:
        with self._lock:
            # Remove the chunk key from the processing set.
            level_gl_data.processing_chunks.remove(chunk_key)
            # Wake up the manager thread to submit new jobs.
            self._wake_chunk_thread()

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
        try:
            chunk_state = chunk_data.chunk_state
            resource_pack = self._resource_pack
            if resource_pack is None:
                self._finish_chunk_mesher(level_gl_data, chunk_key)
                return

            # Do the chunk meshing
            dimension, cx, cz = chunk_key
            buffer, vertex_count = mesh_chunk(
                self._level, resource_pack, dimension, cx, cz
            )

        except Exception as e:
            self._finish_chunk_mesher(level_gl_data, chunk_key)
            display_exception(
                f"Error meshing chunk {chunk_key}.",
                error=str(e),
                traceback=traceback.format_exc(),
            )
        else:
            # queue OpenGL data creation on the main thread.
            log.debug(f"Mesh generated for {chunk_key}")
            self._init_chunk_gl_signal.emit(
                level_gl_data,
                chunk_key,
                chunk_data,
                chunk_state,
                buffer,
                vertex_count,
            )

    def _init_chunk_gl(
        self,
        level_gl_data: LevelGeometryGLData,
        chunk_key: ChunkKey,
        chunk_data: ChunkData,
        chunk_state: int,
        buffer: bytes,
        vertex_count: int,
    ) -> None:
        try:
            with self._lock:
                log.debug(f"Creating OpenGL data for chunk {chunk_key}")
                if level_gl_data.chunks.get(chunk_key) is not chunk_data:
                    # The chunk data was removed during meshing.
                    # This could be because we changed dimension or moved away from the chunk.
                    # In these cases just discard the mesh.
                    return

                if not level_gl_data.context.makeCurrent(self._surface):
                    raise RuntimeError("Could not make context current.")

                f = QOpenGLContext.currentContext().functions()

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

                level_gl_data.context.doneCurrent()
                self.geometry_changed.emit()
        except Exception as e:
            display_exception(
                f"Error creating OpenGL data for chunk {chunk_key}.",
                error=str(e),
                traceback=traceback.format_exc(),
            )
        finally:
            self._finish_chunk_mesher(level_gl_data, chunk_key)
            log.debug(f"Finished creating OpenGL data for chunk {chunk_key}")
