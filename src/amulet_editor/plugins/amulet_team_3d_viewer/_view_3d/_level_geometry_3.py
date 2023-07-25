from __future__ import annotations
import logging
import threading
from typing import Optional, Generator, NamedTuple
from math import floor
import ctypes
from uuid import uuid4, UUID
from threading import Lock, RLock, Condition
from weakref import WeakKeyDictionary, WeakValueDictionary
import warnings
import numpy

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QMatrix4x4, QOpenGLContext, QOffscreenSurface
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
from amulet.api.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.api.chunk import Chunk

from amulet_editor.data.dev._debug import enable_trace
from amulet_editor.models.generic._promise import Promise
from amulet_editor.models.generic._context_switcher import ContextSwitcher

from ._drawable import Drawable
from ._resource_pack import OpenGLResourcePack, get_gl_resource_pack_container, RenderResourcePackContainer

try:
    from .chunk_builder_cy import create_lod0_chunk
except:
    raise Exception(
        "Could not import cython chunk mesher. The cython code must be compiled first."
    )

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)

ChunkKey = tuple[Dimension, int, int]


class SharedChunkVBO(QObject):
    """
    A class holding all the shared chunk data.
    The vbo will be deallocated when this instance is destroyed
    or when the :class:`SharedLevelGeometry` that created it is destroyed.
    """
    vbo: QOpenGLBuffer
    vertex_count: int

    def __init__(self, vbo: QOpenGLBuffer, vertex_count: int):
        super().__init__()
        self.vbo = vbo
        self.vertex_count = vertex_count


class SharedChunkData(QObject):
    """
    The instances of this class belong to the :class:`SharedLevelGeometry` that created them.
    All data will be destroyed when the last reference to the instance is lost
    or when the last reference to the :class:`SharedLevelGeometry` that created it is lost.
    """

    # Constant data
    # The world transform of the data.
    model_transform: QMatrix4x4

    # Variable data
    # The shared OpenGL data.
    # This variable can get modified, you must hold a strong reference to this object and access it from there.
    # It will be None initially until geometry_changed is emitted.
    geometry: Optional[SharedChunkVBO]

    # Signals
    # Emitted when the geometry has been modified.
    geometry_changed = Signal()

    def __init__(self, model_transform: QMatrix4x4):
        super().__init__()
        self.model_transform: QMatrix4x4 = model_transform
        self.geometry = None


class ChunkGenerator(QObject):
    def run(self):
        pass


class SharedLevelGeometry(QObject):
    """
    A class holding the shared level geometry relating to one level.
    """

    # Class variables
    _instances: WeakKeyDictionary[BaseLevel, SharedLevelGeometry] = {}

    # Instance variables
    _level: BaseLevel

    _thread: Optional[QThread]
    _worker: Optional[QObject]

    _context: QOpenGLContext
    _surface: QOffscreenSurface

    _lock: Lock
    # Store the chunk data weakly so that it gets automatically deallocated
    _chunks: WeakValueDictionary[ChunkKey, SharedChunkData]

    @classmethod
    def instance(cls, level: BaseLevel) -> SharedLevelGeometry:
        return cls._instances.setdefault(level, SharedLevelGeometry(level))

    def __init__(self, level: BaseLevel):
        """To get an instance of this class you should use :classmethod:`instance`"""
        super().__init__()
        self._level = level

        # The chunk generation thread
        self._thread = QThread()
        self._thread.start()
        self._worker = None

        self._lock = Lock()
        self._chunks = WeakValueDictionary()

        self._context = QOpenGLContext()
        global_context = QOpenGLContext.globalShareContext()
        if global_context is None:
            raise RuntimeError("Global OpenGL context does not exist.")
        self._context.setShareContext(global_context)
        self._context.create()
        self._surface = QOffscreenSurface()
        self._surface.create()

    def __del__(self):
        # TODO: delete all data
        log.debug("Waiting for chunk generation thread to finish")
        self._thread.quit()
        self._thread.wait()
        log.debug("Chunk generation thread has finished")

    def get_chunk(self, chunk_key: ChunkKey) -> SharedChunkData:
        """Get the geometry for a chunk."""
        with self._lock:
            chunk = self._chunks.get(chunk_key)
            if chunk is None:
                dimension, cx, cz = chunk_key
                transform = QMatrix4x4()
                transform.translate(cx * 16, 0, cz * 16)
                chunk = self._chunks[chunk_key] = SharedChunkData(transform)
                # TODO: create the VBO in the generator thread and set in this object
        return chunk


class WidgetChunkData:
    shared: SharedChunkData
    vbo: Optional[SharedChunkVBO]
    vao: Optional[QOpenGLVertexArrayObject]

    def __init__(self, shared: SharedChunkData):
        self.shared = shared
        self.vbo = None
        self.vao = None


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


class WidgetLevelGeometry(QObject, Drawable):
    """
    A class holding the level geometry data relating to one widget.
    This holds all non-shared data and references to the shared data.
    When this object is deleted it will automatically destroy its own data.

    The methods in this class must only be called from the thread the owner QOpenGLWidget is in.
    """

    _shared: SharedLevelGeometry

    _render_radius: int
    _dimension: Optional[Dimension]
    _camera_chunk: Optional[tuple[int, int]]
    _chunk_finder: Generator[ChunkKey, None, None]

    # OpenGL attributes
    _context: Optional[QOpenGLContext]
    _program: Optional[QOpenGLShaderProgram]
    _matrix_location: Optional[int]
    _texture_location: Optional[int]
    _chunks: set[WidgetChunkData]

    # The geometry has changed and needs repainting.
    changed = Signal()

    def __init__(self, level: BaseLevel):
        super().__init__()
        self._shared = SharedLevelGeometry.instance(level)

        self._render_radius = 5
        self._dimension = None
        self._camera_chunk = None
        self._chunk_finder = empty_iterator()

        self._context = None
        self._program = None
        self._matrix_location = None
        self._texture_location = None

    def initializeGL(self):
        """
        Initialise the opengl state.
        The widget context must be current before calling this.
        This must only be called from the QOpenGLWidget that this instance is associated with.
        """
        context = QOpenGLContext.currentContext()
        if not QOpenGLContext.areSharing(context, QOpenGLContext.globalShareContext()):
            raise RuntimeError("The widget context is not sharing with the global context.")

        # Make sure any old data no longer exists.
        self._destroy_gl()
        self._context = context
        self._context.aboutToBeDestroyed.connect(self._destroy_gl)

        # Initialise the shader
        self._program = QOpenGLShaderProgram()
        self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex,
            """#version 130
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

        self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment,
            """#version 130
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
            }"""
        )

        self._program.link()
        self._program.bind()
        self._matrix_location = self._program.uniformLocation("transformation_matrix")
        self._texture_location = self._program.uniformLocation("image")

    def _destroy_gl(self):
        if self._context is not None:
            if QOpenGLContext.currentContext() is not self._context:
                # Enable the context if it isn't.
                # Use an offscreen surface because the widget surface may no longer exist.
                surface = QOffscreenSurface()
                surface.create()
                if not self._context.makeCurrent(surface):
                    raise RuntimeError("Could not make context current to destroy the OpenGL data.")

            self._program = None
            self._matrix_location = None
            self._texture_location = None
            self._context = None
            self._chunks.clear()

    def __del__(self):
        self._destroy_gl()

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        """
        Draw the level.
        The context must be active before calling this.

        :param projection_matrix: The camera internal projection matrix.
        :param view_matrix: The camera external matrix.
        """
        context = QOpenGLContext.currentContext()
        if context is None or not QOpenGLContext.areSharing(context, self._context):
            raise RuntimeError("Context is not valid")

        # if self._data.resource_pack is None:
        #     # If the resource pack has not been loaded yet then there is nothing to draw.
        #     return
        #
        # with self._data.lock:
        #     # Unload old chunks
        #     for chunk_model in self._data.chunk_models_unload:
        #         chunk_model.vao.destroy()
        #     self._data.chunk_models_unload.clear()
        #
        #     f = QOpenGLContext.currentContext().functions()
        #
        #     for chunk_key, (buffer, buffer_size, vertex_count, transform) in self._data.chunk_data_load.items():
        #         vbo = QOpenGLBuffer()
        #         vbo.create()
        #         vbo.bind()
        #         vbo.allocate(
        #             buffer, buffer_size
        #         )
        #         vbo.release()
        #         self._data.chunk_models_load[chunk_key] = ChunkModel(vbo, vertex_count, transform)
        #     self._data.chunk_data_load.clear()
        #
        #     # Create VAOs for new chunks
        #     for chunk_key, chunk_model in self._data.chunk_models_load.items():
        #         chunk_model.vao = QOpenGLVertexArrayObject()
        #         chunk_model.vao.create()
        #         chunk_model.vao.bind()
        #         chunk_model.vbo.bind()
        #
        #         # vertex coord
        #         f.glEnableVertexAttribArray(0)
        #         f.glVertexAttribPointer(
        #             0, 3, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(0)
        #         )
        #         # texture coord
        #         f.glEnableVertexAttribArray(1)
        #         f.glVertexAttribPointer(
        #             1, 2, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(3 * FloatSize)
        #         )
        #         # texture bounds
        #         f.glEnableVertexAttribArray(2)
        #         f.glVertexAttribPointer(
        #             2, 4, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(5 * FloatSize)
        #         )
        #         # tint
        #         f.glEnableVertexAttribArray(3)
        #         f.glVertexAttribPointer(
        #             3, 3, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(9 * FloatSize)
        #         )
        #
        #         chunk_model.vbo.release()
        #         chunk_model.vao.release()
        #
        #         self._data.chunk_models[chunk_key] = chunk_model
        #     self._data.chunk_models_load.clear()
        #
        #     # Draw the geometry
        #     self._program.bind()
        #
        #     # Init the texture
        #     self._program.setUniformValue1i(self._texture_location, 0)
        #     self._data.resource_pack.get_texture().bind(0)
        #
        #     transform = projection_matrix * view_matrix
        #     for chunk_model in self._data.chunk_models.values():
        #         self._program.setUniformValue(
        #             self._matrix_location,
        #             transform * chunk_model.model_transform
        #         )
        #         chunk_model.vao.bind()
        #         f.glDrawArrays(
        #             GL_TRIANGLES, 0, chunk_model.vertex_count
        #         )
        #         chunk_model.vao.release()
        #
        #     self._program.release()

    def _clear_chunks(self):
        raise NotImplementedError

    def set_dimension(self, dimension: Dimension):
        if dimension != self._dimension:
            self._dimension = dimension
            self._clear_chunks()

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        location = (cx, cz)
        if location != self._camera_chunk:
            self._camera_chunk = location
            # TODO
