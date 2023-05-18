import logging
from typing import Optional, Generator
from threading import Lock
from math import floor
import ctypes

from PySide6.QtCore import QThreadPool, QThread, QWaitCondition, QMutex
from PySide6.QtGui import QMatrix4x4, QOpenGLContext, QOffscreenSurface, QSurface
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

FloatSize = ctypes.sizeof(ctypes.c_float)
GL_FLOAT_INT = int(GL_FLOAT)
GL_FALSE_INT = int(GL_FALSE)

log = logging.getLogger(__name__)

from amulet.api.data_types import Dimension
from amulet.api.level import BaseLevel

from ._drawable import Drawable

ChunkKey = tuple[Dimension, int, int]


_level_context: Optional[QOpenGLContext] = None
_global_lock = Lock()


def _init():
    """Initialise global variables"""
    global _level_context
    with _global_lock:
        if _level_context is None:
            _level_context = QOpenGLContext()
            _level_context.create()


class ContextSwitcher:
    """A utility class to switch to a new context and then switch back."""

    def __init__(self, context: QOpenGLContext, surface: QSurface):
        self._context = context
        self._surface = surface
        self._start_context = None
        self._start_surface = None

    def __enter__(self):
        # Store the start state
        self._start_context = QOpenGLContext.currentContext()
        if self._start_context is not None:
            self._start_surface = self._start_context.surface()

        self._context.makeCurrent(self._surface)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._start_context is None or self._start_surface is None:
            self._context.doneCurrent()
        else:
            self._start_context.makeCurrent(self._start_surface)


class SharedVBO:
    """
    A container for VBO data that can be shared between multiple contexts.
    Constructed with the vbo and the number of vertices in the vbo.
    Once the last reference to this object is lost the VBO will be destroyed.
    """

    def __init__(self, context: QOpenGLContext, vbo: QOpenGLBuffer, vertex_count: int):
        """

        :param context: The context the vbo is defined in
        :param vbo: The vbo
        :param vertex_count: The number of vertices in the vbo
        """
        self._context = context
        self.vbo = vbo
        self.vertex_count = vertex_count

    def _destroy(self):
        # Each context can only be current in one thread so make a temporary context
        temp_surface = QOffscreenSurface()
        temp_context = QOpenGLContext()
        temp_context.create()

        with ContextSwitcher(temp_context, temp_surface):
            self._context.setShareContext(temp_context)
            self.vbo.destroy()

    def __del__(self):
        self._destroy()


def _get_chunk_data() -> SharedVBO:
    raise NotImplementedError


class Chunk:
    def __init__(self, shared_vbo: SharedVBO, model_transform: QMatrix4x4):
        self.shared_vbo: SharedVBO = shared_vbo
        self.model_transform: QMatrix4x4 = model_transform
        self.vao: Optional[QOpenGLVertexArrayObject] = None


def empty_iterator():
    if False:
        yield


def get_grid_spiral(cx: int, cz: int, r: int):
    """A generator that yields a 2D grid spiraling from the centre."""
    sign = 1
    length = 1
    for _ in range(r * 2 + 1):
        for _ in range(length):
            yield cx, cz
            cx += sign
        for _ in range(length):
            yield cx, cz
            cz += sign
        sign *= -1
        length += 1


class LevelGeometry(Drawable):
    def __init__(self, level: BaseLevel):
        self._level = level
        self._dimension: Optional[Dimension] = None
        self._camera_chunk: tuple[int, int] = (0, 0)

        # Near render attributes
        self._near_render_radius = 5
        self._near_program: Optional[QOpenGLShaderProgram] = None
        self._near_matrix_loc: Optional[int] = None

        # A lock to acquire when modifying any of the following objects
        self._near_mutex = QMutex()
        # Once a worker thread has completed all of its jobs it will wait on this condition
        self._near_condition = QWaitCondition()
        # Chunks that should be loaded
        self._near_chunks_todo: Generator[ChunkKey, None, None] = empty_iterator()
        # Storage of chunks being built
        self._near_chunks_wip: set[ChunkKey] = set()
        # Chunks that have been loaded but the context data not initialised.
        self._near_chunks_load: dict[ChunkKey, Chunk] = {}
        # Chunks that can currently be rendered
        self._near_chunks: dict[ChunkKey, Chunk] = {}
        # Chunks that need to be unloaded
        self._near_chunks_unload: list[Chunk] = []

        self._near_thread_pool = QThreadPool()
        self._near_thread_pool.setThreadPriority(QThread.Priority.LowPriority)
        self._near_thread_pool.setMaxThreadCount(4)
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)
        self._near_thread_pool.start(self._chunk_generator)

    def _chunk_generator(self):
        # Initialise the shared context
        _init()
        # Make a temporary context
        temp_surface = QOffscreenSurface()
        temp_context = QOpenGLContext()
        temp_context.create()
        temp_context.makeCurrent(temp_surface)
        # Share the context
        _level_context.setShareContext(temp_context)
        while True:
            # Find a chunk to generate.
            self._near_mutex.lock()
            while True:
                chunk_id = next(self._near_chunks_todo, None)
                if chunk_id is None:
                    # Completed all jobs. Wait until more jobs are added.
                    self._near_condition.wait(self._near_mutex)
                elif (
                    chunk_id not in self._near_chunks_wip and
                    chunk_id not in self._near_chunks_load and
                    chunk_id not in self._near_chunks
                ):
                    break
            self._near_chunks_wip.add(chunk_id)
            self._near_mutex.unlock()

            # Generate the chunk geometry. This can be done in parallel.
            # TODO: Generate the chunk VBO
            shared_vbo = None

            chunk = Chunk(shared_vbo)

            # Get the lock again and add to the loaded dictionary
            self._near_mutex.lock()
            if chunk_id in self._near_chunks_wip:
                self._near_chunks_wip.remove(chunk_id)
                self._near_chunks_load[chunk_id] = chunk
            self._near_mutex.unlock()

    def set_dimension(self, dimension: Dimension):
        if dimension != self._dimension:
            self._near_mutex.lock()
            self._dimension = dimension

            # All the chunks are now invalid so clear them.
            cx, cz = self._camera_chunk
            self._near_chunks_todo = get_grid_spiral(cx, cz, self._near_render_radius)
            self._near_chunks_wip.clear()
            self._near_chunks_load.clear()
            self._near_chunks_unload.extend(self._near_chunks.values())
            self._near_chunks.clear()

            self._near_condition.wakeAll()
            self._near_mutex.unlock()

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        location = (cx, cz)
        if location != self._camera_chunk:
            # Update the chunks
            self._near_mutex.lock()
            self._camera_chunk = cam_cx, cam_cz = location

            max_radius = floor(self._near_render_radius * 1.5)
            min_cx = cam_cx - max_radius
            max_cx = cam_cx + max_radius
            min_cz = cam_cz - max_radius
            max_cz = cam_cz + max_radius

            # Unload all chunks outside the new render distance
            for chunk_key in list(self._near_chunks):
                dimension, cx, cz = chunk_key
                if not (min_cx <= cx <= max_cx and min_cz <= cz <= max_cz):
                    self._near_chunks_unload.append(self._near_chunks.pop(chunk_key))

            # Delete all chunks outside the render distance that have not been loaded yet.
            for chunk_key in list(self._near_chunks_load):
                dimension, cx, cz = chunk_key
                if not (min_cx <= cx <= max_cx and min_cz <= cz <= max_cz):
                    self._near_chunks_load.pop(chunk_key)

            # Stop chunks being generated outside the render distance
            for chunk_key in list(self._near_chunks_wip):
                dimension, cx, cz = chunk_key
                if not (min_cx <= cx <= max_cx and min_cz <= cz <= max_cz):
                    self._near_chunks_wip.remove(chunk_key)

            # Recreate the to do generator
            self._near_chunks_todo = get_grid_spiral(cx, cz, self._near_render_radius)

            self._near_condition.wakeAll()
            self._near_mutex.unlock()

    def initializeGL(self):
        """Initialise the opengl state. This should be run once for each context."""
        _init()
        _level_context.setShareContext(QOpenGLContext.currentContext())

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

    def destroyGL(self):
        """Destroy the OpenGL data tied to the context. This must be called before destruction."""
        self._near_mutex.lock()

        # Destroy the VAOs from the old context.
        chunks = self._near_chunks.copy()
        self._near_chunks.clear()
        for chunk in chunks.values():
            chunk.vao.destroy()
        self._near_chunks_load.update(chunks)

        self._near_mutex.unlock()

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        self._near_mutex.lock()

        # Unload old chunks
        for chunk in self._near_chunks_unload:
            chunk.vao.destroy()
        self._near_chunks_unload.clear()

        f = QOpenGLContext.currentContext().functions()

        # Create VAOs for new chunks
        for chunk_key, chunk in self._near_chunks_load.items():
            chunk.vao = QOpenGLVertexArrayObject()
            chunk.vao.create()
            chunk.vao.bind()
            chunk.shared_vbo.vbo.bind()

            f.glEnableVertexAttribArray(0)
            f.glEnableVertexAttribArray(1)
            f.glVertexAttribPointer(
                0, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(0)
            )
            f.glVertexAttribPointer(
                1, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(3 * FloatSize)
            )

            chunk.shared_vbo.vbo.release()
            chunk.vao.release()

            self._near_chunks[chunk_key] = chunk
        self._near_chunks_load.clear()

        # Draw the geometry
        self._near_program.bind()
        transform = projection_matrix * view_matrix
        for chunk in self._near_chunks.values():
            self._near_program.setUniformValue(
                self._near_matrix_loc,
                transform * chunk.model_transform
            )
            chunk.vao.bind()
            f.glDrawArrays(
                GL_TRIANGLES, 0, chunk.shared_vbo.vertex_count
            )
            chunk.vao.release()

        self._near_program.release()

        self._near_mutex.unlock()
