import logging
import threading
from typing import Optional, Generator
from math import floor
import ctypes
from uuid import uuid4, UUID
from threading import RLock, Condition
import numpy

from PySide6.QtCore import QThread, Signal, QObject
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
from amulet.api.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.api.chunk import Chunk

from amulet_editor.data.dev._debug import enable_trace

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


class LevelGeometryData(QObject):
    """Data shared by ChunkGenerator workers."""
    level: BaseLevel
    resource_pack_container: RenderResourcePackContainer
    resource_pack: Optional[OpenGLResourcePack]

    dimension: Optional[Dimension]
    camera_chunk: tuple[int, int]

    render_radius: int

    lock: RLock
    condition: Condition
    chunks_todo: Generator[ChunkKey, None, None]
    chunks_todo_changed: set[ChunkKey]
    chunks_wip: dict[ChunkKey, UUID]
    chunk_data_load: dict[ChunkKey, tuple[bytes, int, int, QMatrix4x4]]
    chunk_models_load: dict[ChunkKey, ChunkModel]
    chunk_models: dict[ChunkKey, ChunkModel]
    chunk_models_unload: list[ChunkModel]

    changed = Signal()

    def __init__(self, level: BaseLevel):
        super().__init__()
        self.level = level
        self.resource_pack_container = get_gl_resource_pack_container(level)
        self.resource_pack = self.resource_pack_container.resource_pack if self.resource_pack_container.loaded else None
        self.resource_pack_container.changed.connect(self._resource_pack_changed)

        self.dimension = None
        self.camera_chunk = (0, 0)

        # Near render attributes
        self.render_radius = 50

        # A lock to acquire when modifying any of the following objects
        self.lock = RLock()
        # Once a worker thread has completed all of its jobs it will wait on this condition
        self.condition = Condition(self.lock)
        # Chunks that should be loaded
        self.chunks_todo = empty_iterator()
        # Another container is required to differentiate chunks that have changed from those that just need generating.
        self.chunks_todo_changed = set()
        # Storage of chunks being built
        self.chunks_wip = {}
        # Chunk data generated but not uploaded to the GPU
        self.chunk_data_load = {}
        # Chunks that have been loaded but the context data not initialised.
        self.chunk_models_load = {}
        # Chunks that can currently be rendered
        self.chunk_models = {}
        # Chunks that need to be unloaded
        self.chunk_models_unload = []

        self.running = False

    def _clear_chunks(self):
        """Clear all the chunks."""
        with self.lock:
            self.chunk_models_unload.extend(self.chunk_models.values())
            self.chunk_models.clear()
            self.chunk_models_load.clear()
            self.chunk_data_load.clear()
            self.chunks_wip.clear()
            cx, cz = self.camera_chunk
            self.chunks_todo = get_grid_spiral(self.dimension, cx, cz, self.render_radius)
            self.chunks_todo_changed.clear()

            self.condition.notify_all()
            self.changed.emit()

    def _resource_pack_changed(self):
        self.resource_pack = self.resource_pack_container.resource_pack
        self._clear_chunks()

    def set_dimension(self, dimension: Dimension):
        if dimension != self.dimension:
            with self.lock:
                self.dimension = dimension
                self._clear_chunks()

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        location = (cx, cz)
        if location != self.camera_chunk:
            # Update the chunks
            with self.lock:
                self.camera_chunk = location

                max_radius = floor(self.render_radius * 1.5)

                keep_chunks = set(get_grid_spiral(self.dimension, cx, cz, max_radius))

                # Unload all chunks outside the new render distance
                for chunk_key in set(self.chunk_models).difference(keep_chunks):
                    self.chunk_models_unload.append(self.chunk_models.pop(chunk_key))

                # Delete all chunks outside the render distance that have not been loaded yet.
                for chunk_key in set(self.chunk_data_load).difference(keep_chunks):
                    self.chunk_data_load.pop(chunk_key)
                for chunk_key in set(self.chunk_models_load).difference(keep_chunks):
                    self.chunk_models_load.pop(chunk_key)

                # Stop chunks being generated outside the render distance
                for chunk_key in set(self.chunks_wip).difference(keep_chunks):
                    self.chunks_wip.pop(chunk_key)

                # Recreate the to do generator
                self.chunks_todo = get_grid_spiral(self.dimension, cx, cz, self.render_radius)
                # Keep the intersection of changed chunks with those in the extended render distance
                self.chunks_todo_changed = self.chunks_todo_changed.intersection(keep_chunks)

                self.condition.notify_all()
                self.changed.emit()


class ChunkGenerator(QObject):
    """A chunk generator worker."""
    def __init__(self, data: LevelGeometryData):
        super().__init__()
        self.data = data

    def chunk_generator(self):
        try:
            enable_trace()
            log.debug(f"Chunk generator thread {threading.get_ident()}: Starting")
            # Wait for a resource pack to be set
            with self.data.lock:
                while self.data.resource_pack is None and self.data.running:
                    self.data.condition.wait()
                # Exit the thread if the user closes the application before the resource pack is loaded.
                if not self.data.running:
                    log.debug(f"Chunk generator thread {threading.get_ident()}: Exiting")
                    return

            # Initialise the shared context
            while True:
                # Find a chunk to generate.
                with self.data.lock:
                    while True:
                        log.debug("searching")
                        if not self.data.running:
                            log.debug(f"Chunk generator thread {threading.get_ident()}: Exiting")
                            return

                        if self.data.chunks_todo_changed:
                            chunk_id = self.data.chunks_todo_changed.pop()
                            break
                        else:
                            chunk_id = next(self.data.chunks_todo, None)
                            if chunk_id is None:
                                # Completed all jobs. Wait until more jobs are added.
                                log.debug(f"Chunk generator thread {threading.get_ident()}: Waiting")
                                self.data.condition.wait()
                                if not self.data.running:
                                    log.debug(f"Chunk generator thread {threading.get_ident()}: Exiting")
                                    return
                            elif (
                                    chunk_id in self.data.chunk_models or
                                    chunk_id in self.data.chunk_models_load or
                                    chunk_id in self.data.chunk_data_load or
                                    chunk_id in self.data.chunks_wip
                            ):
                                # If the chunk is already loaded or being loaded then skip it
                                continue
                            else:
                                break

                    log.debug(f"Generating geometry for chunk {chunk_id}")
                    gen_id = uuid4()
                    self.data.chunks_wip[chunk_id] = gen_id

                # Generate the chunk geometry. This can be done in parallel.
                dimension, cx, cz = chunk_id

                buffer = b""
                try:
                    chunk = self.data.level.get_chunk(cx, cz, dimension)
                except ChunkDoesNotExist:
                    # TODO: Add void geometry
                    continue
                except ChunkLoadError:
                    # TODO: Add error geometry
                    log.exception(f"Error loading chunk {chunk_id}", exc_info=True)
                    continue
                    # self._create_error_geometry()
                else:
                    chunk_verts, chunk_verts_translucent = create_lod0_chunk(
                        self.data.resource_pack,
                        numpy.zeros(3, dtype=numpy.int32),
                        self._sub_chunks(dimension, cx, cz, chunk),
                        chunk.block_palette,
                    )
                    verts = chunk_verts + chunk_verts_translucent
                    if verts:
                        buffer = numpy.concatenate(verts).tobytes()

                buffer_size = len(buffer)
                vertex_count = buffer_size // (12 * FloatSize)

                transform = QMatrix4x4()
                transform.translate(cx * 16, 0, cz * 16)

                log.debug(f"Generated array for {chunk_id}")

                # Get the lock again and add to the loaded dictionary
                with self.data.lock:
                    if self.data.chunks_wip.get(chunk_id, None) == gen_id:
                        # If generation is canceled this will be None
                        # If a newer generation has started it will be different
                        self.data.chunks_wip.pop(chunk_id)
                        self.data.chunk_data_load[chunk_id] = (buffer, buffer_size, vertex_count, transform)
                        self.data.changed.emit()
                        log.debug(f"Generated chunk {chunk_id}")
        except Exception as e:
            log.exception(e)

    def _sub_chunks(self, dimension: Dimension, cx: int, cz: int, chunk: Chunk) -> list[tuple[numpy.ndarray, int]]:
        """
        Create sub-chunk arrays that extend into the neighbour sub-chunks by one block.

        :param dimension: The dimension the chunk came from
        :param cx: The chunk x coordinate of the chunk
        :param cz: The chunk z coordinate of the chunk
        :param chunk: The chunk object
        :return: A list of tuples containing the larger block array and the location of the sub-chunk
        """
        blocks = chunk.blocks
        sub_chunks = []
        neighbour_chunks = {}
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            try:
                neighbour_chunks[(dx, dz)] = self.data.level.get_chunk(
                    cx + dx, cz + dz, dimension
                ).blocks
            except ChunkLoadError:
                continue

        for cy in blocks.sub_chunks:
            sub_chunk = blocks.get_sub_chunk(cy)
            larger_blocks = numpy.zeros(
                sub_chunk.shape + numpy.array((2, 2, 2)), sub_chunk.dtype
            )
            # if self._limit_bounds:
            #     sub_chunk_box = SelectionBox.create_sub_chunk_box(cx, cy, cz)
            #     if self._level.bounds(self.dimension).intersects(sub_chunk_box):
            #         boxes = self._level.bounds(self.dimension).intersection(
            #             sub_chunk_box
            #         )
            #         for box in boxes.selection_boxes:
            #             larger_blocks[1:-1, 1:-1, 1:-1][
            #                 box.sub_chunk_slice(self.cx, cy, self.cz)
            #             ] = sub_chunk[box.sub_chunk_slice(self.cx, cy, self.cz)]
            #     else:
            #         continue
            # else:
            #     larger_blocks[1:-1, 1:-1, 1:-1] = sub_chunk
            larger_blocks[1:-1, 1:-1, 1:-1] = sub_chunk
            for chunk_offset, neighbour_blocks in neighbour_chunks.items():
                if cy not in neighbour_blocks:
                    continue
                if chunk_offset == (-1, 0):
                    larger_blocks[0, 1:-1, 1:-1] = neighbour_blocks.get_sub_chunk(cy)[
                        -1, :, :
                    ]
                elif chunk_offset == (1, 0):
                    larger_blocks[-1, 1:-1, 1:-1] = neighbour_blocks.get_sub_chunk(cy)[
                        0, :, :
                    ]
                elif chunk_offset == (0, -1):
                    larger_blocks[1:-1, 1:-1, 0] = neighbour_blocks.get_sub_chunk(cy)[
                        :, :, -1
                    ]
                elif chunk_offset == (0, 1):
                    larger_blocks[1:-1, 1:-1, -1] = neighbour_blocks.get_sub_chunk(cy)[
                        :, :, 0
                    ]
            if cy - 1 in blocks:
                larger_blocks[1:-1, 0, 1:-1] = blocks.get_sub_chunk(cy - 1)[:, -1, :]
            if cy + 1 in blocks:
                larger_blocks[1:-1, -1, 1:-1] = blocks.get_sub_chunk(cy + 1)[:, 0, :]
            sub_chunks.append((larger_blocks, cy * 16))
        return sub_chunks


class LevelGeometry(QObject, Drawable):
    _program: Optional[QOpenGLShaderProgram]
    _matrix_location: Optional[int]
    _texture_location: Optional[int]

    _thread: Optional[QThread]
    _worker: Optional[ChunkGenerator]

    changed = Signal()

    def __init__(self, level: BaseLevel):
        super().__init__()
        self._data = LevelGeometryData(level)
        self._data.changed.connect(self.changed)

        self._program = None
        self._matrix_location = None
        self._texture_location = None

        self._thread = None
        self._worker = None

    def start(self):
        if not self._data.running:
            self._data.running = True
            self._thread = QThread()
            self._worker = ChunkGenerator(self._data)
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.chunk_generator)
            self._thread.start()

    def stop(self):
        self._data.running = False
        with self._data.lock:
            self._data.condition.notify_all()
        log.debug("Waiting for chunk generation thread to finish")
        self._thread.quit()
        self._thread.wait()
        log.debug("Chunk generation thread has finished")

    def set_dimension(self, dimension: Dimension):
        self._data.set_dimension(dimension)

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        self._data.set_location(cx, cz)

    def initializeGL(self):
        """Initialise the opengl state. This should be run once for each context."""
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

    def destroyGL(self):
        """Destroy the OpenGL data tied to the context. This must be called before destruction."""
        with self._data.lock:
            log.debug("destroy GL")
            # Destroy the VAOs from the old context.
            chunks = self._data.chunk_models.copy()
            self._data.chunk_models.clear()
            for chunk in chunks.values():
                chunk.vao.destroy()
            self._data.chunk_models_load.update(chunks)

            self._data.running = False
            self._data.condition.notify_all()

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        if self._data.resource_pack is None:
            # If the resource pack has not been loaded yet then there is nothing to draw.
            return

        with self._data.lock:
            # Unload old chunks
            for chunk_model in self._data.chunk_models_unload:
                chunk_model.vao.destroy()
            self._data.chunk_models_unload.clear()

            f = QOpenGLContext.currentContext().functions()

            for chunk_key, (buffer, buffer_size, vertex_count, transform) in self._data.chunk_data_load.items():
                vbo = QOpenGLBuffer()
                vbo.create()
                vbo.bind()
                vbo.allocate(
                    buffer, buffer_size
                )
                vbo.release()
                self._data.chunk_models_load[chunk_key] = ChunkModel(vbo, vertex_count, transform)
            self._data.chunk_data_load.clear()

            # Create VAOs for new chunks
            for chunk_key, chunk_model in self._data.chunk_models_load.items():
                chunk_model.vao = QOpenGLVertexArrayObject()
                chunk_model.vao.create()
                chunk_model.vao.bind()
                chunk_model.vbo.bind()

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

                chunk_model.vbo.release()
                chunk_model.vao.release()

                self._data.chunk_models[chunk_key] = chunk_model
            self._data.chunk_models_load.clear()

            # Draw the geometry
            self._program.bind()

            # Init the texture
            self._program.setUniformValue1i(self._texture_location, 0)
            self._data.resource_pack.get_texture().bind(0)

            transform = projection_matrix * view_matrix
            for chunk_model in self._data.chunk_models.values():
                self._program.setUniformValue(
                    self._matrix_location,
                    transform * chunk_model.model_transform
                )
                chunk_model.vao.bind()
                f.glDrawArrays(
                    GL_TRIANGLES, 0, chunk_model.vertex_count
                )
                chunk_model.vao.release()

            self._program.release()
