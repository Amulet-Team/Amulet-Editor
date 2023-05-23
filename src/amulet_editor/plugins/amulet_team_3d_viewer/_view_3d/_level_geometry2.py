import logging
from typing import Optional, Generator
from math import floor
import ctypes
from uuid import uuid4, UUID
from threading import Lock, Condition

from PySide6.QtCore import QThreadPool, QThread
from PySide6.QtGui import QMatrix4x4, QOpenGLContext
from PySide6.QtOpenGL import (
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLShaderProgram,
    QOpenGLShader
)
from shiboken6 import VoidPtr
from OpenGL.GL import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
)

from amulet.api.data_types import Dimension
from amulet.api.level import BaseLevel

from ._drawable import Drawable
from ._logo import Logo

FloatSize = ctypes.sizeof(ctypes.c_float)
GL_FLOAT_INT = int(GL_FLOAT)
GL_FALSE_INT = int(GL_FALSE)

log = logging.getLogger(__name__)

ChunkKey = tuple[Dimension, int, int]


_logo = Logo()


class ChunkModel:
    vao: Optional[QOpenGLVertexArrayObject]
    vbo: QOpenGLBuffer
    vertex_count: int
    model_transform: QMatrix4x4

    def __init__(self, vbo: QOpenGLBuffer, vertex_count: int, model_transform: QMatrix4x4, vao: Optional[QOpenGLVertexArrayObject] = None):
        self.vao = vao
        self.vbo = vbo
        self.vertex_count = vertex_count
        self.model_transform: QMatrix4x4 = model_transform


def empty_iterator():
    if False:
        yield


def get_grid_spiral(dimension: Dimension, cx: int, cz: int, r: int) -> Generator[ChunkKey, None, None]:
    """A generator that yields a 2D grid spiraling from the centre."""
    sign = 1
    length = 1
    for _ in range(r * 2 + 1):
        for _ in range(length):
            yield dimension, cx, cz
            cx += sign
        for _ in range(length):
            yield dimension, cx, cz
            cz += sign
        sign *= -1
        length += 1


class LevelGeometry(Drawable):
    _level: BaseLevel
    _dimension: Optional[Dimension]
    _camera_chunk: tuple[int, int]

    _near_render_radius: int
    _near_program: Optional[QOpenGLShaderProgram]
    _near_matrix_loc: Optional[int]

    _near_lock: Lock
    _near_condition: Condition
    _near_chunks_todo: Generator[ChunkKey, None, None]
    _near_chunks_todo_changed: set[ChunkKey]
    _near_chunks_wip: dict[ChunkKey, UUID]
    _near_chunk_data_load: dict[ChunkKey, tuple[bytes, int, int, QMatrix4x4]]
    _near_chunk_models_load: dict[ChunkKey, ChunkModel]
    _near_chunk_models: dict[ChunkKey, ChunkModel]
    _near_chunk_models_unload: list[ChunkModel]
    _near_thread_pool: QThreadPool

    def __init__(self, level: BaseLevel):
        self._level = level
        self._dimension = None
        self._camera_chunk = (0, 0)

        # Near render attributes
        self._near_render_radius = 5
        self._near_program = None
        self._near_matrix_loc = None

        # A lock to acquire when modifying any of the following objects
        self._near_lock = Lock()
        # Once a worker thread has completed all of its jobs it will wait on this condition
        self._near_condition = Condition(self._near_lock)
        # Chunks that should be loaded
        self._near_chunks_todo = empty_iterator()
        # Another container is required to differentiate chunks that have changed from those that just need generating.
        self._near_chunks_todo_changed = set()
        # Storage of chunks being built
        self._near_chunks_wip = {}
        # Chunk data generated but not uploaded to the GPU
        self._near_chunk_data_load = {}
        # Chunks that have been loaded but the context data not initialised.
        self._near_chunk_models_load = {}
        # Chunks that can currently be rendered
        self._near_chunk_models = {}
        # Chunks that need to be unloaded
        self._near_chunk_models_unload = []

        self._exit = False
        self._near_thread_pool = QThreadPool()
        self._near_thread_pool.setThreadPriority(QThread.Priority.LowPriority)
        self._near_thread_pool.setMaxThreadCount(4)

    def _chunk_generator(self):
        try:
            # Initialise the shared context
            while True:
                # Find a chunk to generate.
                with self._near_lock:
                    while True:
                        log.debug("searching")
                        if self._exit:
                            log.debug("Exiting generator thread")
                            return

                        if self._near_chunks_todo_changed:
                            chunk_id = self._near_chunks_todo_changed.pop()
                            break
                        else:
                            chunk_id = next(self._near_chunks_todo, None)
                            if chunk_id is not None and (
                                chunk_id in self._near_chunk_models or
                                chunk_id in self._near_chunk_models_load or
                                chunk_id in self._near_chunk_data_load or
                                chunk_id in self._near_chunks_wip
                            ):
                                # If the chunk is already loaded or being loaded then skip it
                                continue

                            if chunk_id is None:
                                # Completed all jobs. Wait until more jobs are added.
                                log.debug("waiting")
                                self._near_condition.wait()
                            else:
                                break

                    log.debug(f"Generating geometry for chunk {chunk_id}")
                    gen_id = uuid4()
                    self._near_chunks_wip[chunk_id] = gen_id

                # Generate the chunk geometry. This can be done in parallel.
                dimension, cx, cz = chunk_id

                buffer = _logo.const_data()
                buffer_size = _logo.count() * FloatSize
                vertex_count = _logo.vertex_count()

                transform = QMatrix4x4()
                transform.translate(-cx * 16, 0, -cz * 16)

                log.debug(f"Generated array for {chunk_id}")

                # Get the lock again and add to the loaded dictionary
                with self._near_lock:
                    if self._near_chunks_wip.get(chunk_id, None) == gen_id:
                        # If generation is canceled this will be None
                        # If a newer generation has started it will be different
                        self._near_chunks_wip.pop(chunk_id)
                        self._near_chunk_data_load[chunk_id] = (buffer, buffer_size, vertex_count, transform)
                        log.debug(f"Generated chunk {chunk_id}")
        except Exception as e:
            log.exception(e)

    def set_dimension(self, dimension: Dimension):
        if dimension != self._dimension:
            with self._near_lock:
                self._dimension = dimension

                # All the chunks are now invalid so clear them.
                self._near_chunk_models_unload.extend(self._near_chunk_models.values())
                self._near_chunk_models.clear()
                self._near_chunk_models_load.clear()
                self._near_chunk_data_load.clear()
                self._near_chunks_wip.clear()
                cx, cz = self._camera_chunk
                self._near_chunks_todo = get_grid_spiral(self._dimension, cx, cz, self._near_render_radius)
                self._near_chunks_todo_changed.clear()

                self._near_condition.notify_all()

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        location = (cx, cz)
        if location != self._camera_chunk:
            # Update the chunks
            with self._near_lock:
                self._camera_chunk = location

                max_radius = floor(self._near_render_radius * 1.5)

                keep_chunks = set(get_grid_spiral(self._dimension, cx, cz, max_radius))

                # Unload all chunks outside the new render distance
                for chunk_key in set(self._near_chunk_models).difference(keep_chunks):
                    self._near_chunk_models_unload.append(self._near_chunk_models.pop(chunk_key))

                # Delete all chunks outside the render distance that have not been loaded yet.
                for chunk_key in set(self._near_chunk_data_load).difference(keep_chunks):
                    self._near_chunk_data_load.pop(chunk_key)
                for chunk_key in set(self._near_chunk_models_load).difference(keep_chunks):
                    self._near_chunk_models_load.pop(chunk_key)

                # Stop chunks being generated outside the render distance
                for chunk_key in set(self._near_chunks_wip).difference(keep_chunks):
                    self._near_chunks_wip.pop(chunk_key)

                # Recreate the to do generator
                self._near_chunks_todo = get_grid_spiral(self._dimension, cx, cz, self._near_render_radius)
                # Keep the intersection of changed chunks with those in the extended render distance
                self._near_chunks_todo_changed = self._near_chunks_todo_changed.intersection(keep_chunks)

                self._near_condition.notify_all()

    def initializeGL(self):
        """Initialise the opengl state. This should be run once for each context."""
        # Initialise the shader
        self._near_program = QOpenGLShaderProgram()
        self._near_program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex,
            """#version 130
            in vec3 position;

            uniform mat4 transformation_matrix;

            void main() {
               gl_Position = transformation_matrix * vec4(position, 1.0);
            }""",
        )
        self._near_program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment,
            """#version 130
            out vec4 fragColor;

            void main() {
               fragColor = vec4(1.0, 1.0, 1.0, 1.0);
            }""",
        )
        self._near_program.link()
        self._near_program.bind()
        self._near_matrix_loc = self._near_program.uniformLocation("transformation_matrix")

        self._exit = False
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)

    def destroyGL(self):
        """Destroy the OpenGL data tied to the context. This must be called before destruction."""
        with self._near_lock:
            log.debug("destroy GL")
            # Destroy the VAOs from the old context.
            chunks = self._near_chunk_models.copy()
            self._near_chunk_models.clear()
            for chunk in chunks.values():
                chunk.vao.destroy()
            self._near_chunk_models_load.update(chunks)

            self._exit = True
            self._near_condition.notify_all()

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        with self._near_lock:
            # Unload old chunks
            for chunk_model in self._near_chunk_models_unload:
                chunk_model.vao.destroy()
            self._near_chunk_models_unload.clear()

            f = QOpenGLContext.currentContext().functions()

            for chunk_key, (buffer, buffer_size, vertex_count, transform) in self._near_chunk_data_load.items():
                vbo = QOpenGLBuffer()
                vbo.create()
                vbo.bind()
                vbo.allocate(
                    buffer, buffer_size
                )
                vbo.release()
                chunk_model = ChunkModel(vbo, vertex_count, transform)
                self._near_chunk_models_load[chunk_key] = chunk_model

            # Create VAOs for new chunks
            for chunk_key, chunk_model in self._near_chunk_models_load.items():
                chunk_model.vao = QOpenGLVertexArrayObject()
                chunk_model.vao.create()
                chunk_model.vao.bind()
                chunk_model.vbo.bind()

                f.glEnableVertexAttribArray(0)
                f.glEnableVertexAttribArray(1)
                f.glVertexAttribPointer(
                    0, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(0)
                )
                f.glVertexAttribPointer(
                    1, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(3 * FloatSize)
                )

                chunk_model.vbo.release()
                chunk_model.vao.release()

                self._near_chunk_models[chunk_key] = chunk_model
            self._near_chunk_models_load.clear()

            # Draw the geometry
            self._near_program.bind()
            transform = projection_matrix * view_matrix
            for chunk_model in self._near_chunk_models.values():
                self._near_program.setUniformValue(
                    self._near_matrix_loc,
                    transform * chunk_model.model_transform
                )
                chunk_model.vao.bind()
                f.glDrawArrays(
                    GL_TRIANGLES, 0, chunk_model.vertex_count
                )
                chunk_model.vao.release()

            self._near_program.release()
