from __future__ import annotations
import logging
from typing import Optional, Generator, Callable, Iterator
import ctypes
from threading import Lock
from weakref import WeakKeyDictionary, WeakValueDictionary, ref
from collections.abc import MutableMapping
import bisect
import numpy

from PySide6.QtCore import QThread, Signal, QObject, Slot, QTimer, QCoreApplication
from PySide6.QtGui import QMatrix4x4, QOpenGLContext, QOffscreenSurface
from PySide6.QtOpenGL import (
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLShaderProgram,
    QOpenGLShader,
    QOpenGLTexture,
)
from shiboken6 import VoidPtr, isValid
from OpenGL.GL import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_CULL_FACE,
    GL_BACK,
    GL_DEPTH_TEST,
    GL_LEQUAL,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
)

from amulet.api.data_types import Dimension
from amulet.api.level import BaseLevel
from amulet.api.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.api.chunk import Chunk

from ._drawable import Drawable
from ._resource_pack import (
    OpenGLResourcePack,
    get_gl_resource_pack_container,
)
from amulet_editor.application._invoke import invoke

try:
    from .chunk_builder_cy import create_lod0_chunk
except:
    raise Exception(
        "Could not import cython chunk mesher. The cython code must be compiled first."
    )

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)

ChunkKey = tuple[Dimension, int, int]


class SharedVBOManager(QObject):
    """
    This class manages creating and destroying VBOs so that you don't have to.
    The VBO is created in a context that shares the global share context. Creation is done on the main thread.
    All methods are thread safe.
    """

    _context: QOpenGLContext
    _surface: QOffscreenSurface
    _vbos: set[QOpenGLBuffer]

    def __init__(self):
        """Use new class method"""
        if QThread.currentThread() is not QCoreApplication.instance().thread():
            raise RuntimeError(
                "SharedVBOManager must be constructed on the main thread."
            )

        super().__init__()
        context = self._context = QOpenGLContext()
        global_context = QOpenGLContext.globalShareContext()
        if global_context is None:
            raise RuntimeError("Global OpenGL context does not exist.")
        self._context.setShareContext(global_context)
        self._context.create()

        # Create the surface
        surface = self._surface = QOffscreenSurface()
        self._surface.create()

        lock = self._lock = Lock()
        vbos = self._vbos = set()

        def destroy():
            with lock:
                if not context.makeCurrent(surface):
                    raise RuntimeError("Could not make context current.")

                for vbo in vbos:
                    vbo.destroy()
                vbos.clear()

                context.doneCurrent()

        self.destroyed.connect(destroy)

    def create_vbo(self, buffer: bytes) -> QOpenGLBuffer:
        def create_vbo():
            with self._lock:
                start_context = QOpenGLContext.currentContext()
                start_surface = None
                if start_context is not None:
                    start_surface = start_context.surface()
                    start_context.doneCurrent()

                try:
                    if not self._context.makeCurrent(self._surface):
                        raise RuntimeError("Could not make context current.")

                    vbo = QOpenGLBuffer()
                    vbo.create()
                    vbo.bind()
                    vbo.allocate(buffer, len(buffer))
                    vbo.release()
                    self._vbos.add(vbo)
                    self._context.doneCurrent()

                finally:
                    if start_context is not None and not start_context.makeCurrent(
                        start_surface
                    ):
                        raise RuntimeError("Could not make original context current.")

                return vbo

        return invoke(create_vbo)

    def destroy_vbo(self, vbo: QOpenGLBuffer):
        def destroy_vbo():
            with self._lock:
                start_context = QOpenGLContext.currentContext()
                start_surface = None
                if start_context is not None:
                    start_surface = start_context.surface()
                    start_context.doneCurrent()

                try:
                    if vbo not in self._vbos:
                        raise RuntimeError(
                            "vbo was not created by this class or has already been destroyed."
                        )

                    if not self._context.makeCurrent(self._surface):
                        raise RuntimeError("Could not make context current.")
                    vbo.destroy()
                    self._context.doneCurrent()
                    log.debug("Destroyed vbo")

                finally:
                    if start_context is not None and not start_context.makeCurrent(
                        start_surface
                    ):
                        raise RuntimeError("Could not make original context current.")

        invoke(destroy_vbo)


class SharedChunkGeometry(QObject):
    """
    A class holding all the shared chunk data.
    The vbo will be deallocated when this instance is destroyed.
    """

    vbo: QOpenGLBuffer
    vertex_count: int
    _resource_pack: OpenGLResourcePack
    texture: QOpenGLTexture

    def __init__(
        self, vbo: QOpenGLBuffer, vertex_count: int, resource_pack: OpenGLResourcePack
    ):
        super().__init__()
        self.vbo = vbo
        self.vertex_count = vertex_count
        self._resource_pack = resource_pack
        self.texture = self._resource_pack.get_texture()


class SharedChunkData(QObject):
    """
    The instances of this class belong to the :class:`SharedLevelGeometry` that created them.
    All data will be destroyed when the last reference to the instance is lost.
    """

    # Constant data
    # The world transform of the data.
    model_transform: QMatrix4x4

    # Variable data
    # The shared OpenGL data.
    # This variable can get modified, you must hold a strong reference to this object and access it from there.
    # It may be None initially until geometry_changed is emitted.
    geometry: Optional[SharedChunkGeometry]

    # Signals
    # Emitted when the geometry has been modified.
    geometry_changed = Signal()

    def __init__(self, model_transform: QMatrix4x4):
        super().__init__()
        self.model_transform: QMatrix4x4 = model_transform
        self.geometry = None


class ChunkGeneratorWorker(QObject):
    """
    This object exists in a secondary thread so that chunk generation does not block the main thread.
    The OpenGL calls need to be done on the main thread.
    """

    def __init__(self):
        super().__init__()
        self.generate_chunk.connect(self._generate_chunk)

    generate_chunk = Signal(object, object, object, object)

    @Slot(object, object, object, object)
    def _generate_chunk(
        self,
        level: BaseLevel,
        vbo_manager: SharedVBOManager,
        chunk_key: ChunkKey,
        chunk_data: SharedChunkData,
    ):
        try:
            resource_pack_container = get_gl_resource_pack_container(level)
            if not resource_pack_container.loaded:
                # The resource pack does not exist yet so push the job to the back of the queue
                QTimer.singleShot(
                    100,
                    lambda: self.generate_chunk.emit(
                        level, vbo_manager, chunk_key, chunk_data
                    ),
                )
                return

            resource_pack = resource_pack_container.resource_pack

            dimension, cx, cz = chunk_key

            buffer = b""
            try:
                chunk = level.get_chunk(cx, cz, dimension)
            except ChunkDoesNotExist:
                # TODO: Add void geometry
                pass
            except ChunkLoadError:
                # TODO: Add error geometry
                log.exception(f"Error loading chunk {chunk_key}", exc_info=True)
                pass
                # self._create_error_geometry()
            else:
                chunk_verts, chunk_verts_translucent = create_lod0_chunk(
                    resource_pack,
                    numpy.zeros(3, dtype=numpy.int32),
                    self._sub_chunks(level, dimension, cx, cz, chunk),
                    chunk.block_palette,
                )
                verts = chunk_verts + chunk_verts_translucent
                if verts:
                    buffer = numpy.concatenate(verts).tobytes()

            log.debug(f"Generated array for {chunk_key}")

            vbo = vbo_manager.create_vbo(buffer)

            vertex_count = len(buffer) // (12 * FloatSize)

            chunk_data.geometry = SharedChunkGeometry(vbo, vertex_count, resource_pack)
            # When the container gets garbage collected, destroy the vbo
            chunk_data.geometry.destroyed.connect(lambda: vbo_manager.destroy_vbo(vbo))
            chunk_data.geometry_changed.emit()

            log.debug(f"Generated chunk {chunk_key}")
        except Exception as e:
            log.exception(e)

    def _sub_chunks(
        self, level: BaseLevel, dimension: Dimension, cx: int, cz: int, chunk: Chunk
    ) -> list[tuple[numpy.ndarray, int]]:
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
                neighbour_chunks[(dx, dz)] = level.get_chunk(
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
            #     if level.bounds(self.dimension).intersects(sub_chunk_box):
            #         boxes = level.bounds(self.dimension).intersection(
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


class ChunkGenerator(QObject):
    _thread: QThread
    _worker: ChunkGeneratorWorker

    def __init__(self):
        super().__init__()
        thread = self._thread = QThread()
        self._thread.start()
        self._worker = ChunkGeneratorWorker()
        self._worker.moveToThread(self._thread)

        def destroy():
            self._worker.deleteLater()
            log.debug("Waiting for chunk generation thread to finish")
            thread.quit()
            thread.wait()
            log.debug("Chunk generation thread has finished")
            log.debug("destroyed ChunkGenerator")

        self.destroyed.connect(destroy)
        QCoreApplication.instance().aboutToQuit.connect(self.deleteLater)

    def generate_chunk(
        self,
        level: BaseLevel,
        vbo_manager: SharedVBOManager,
        chunk_key: ChunkKey,
        chunk: SharedChunkData,
    ):
        """
        Async function to generate the chunk VBO.

        :param level: The level to pull chunks from.
        :param vbo_manager: The instance that will manage vbo creation.
        :param chunk_key: The key of the chunk to get.
        :param chunk: The SharedChunkData to store the value in and notify through.
        :return: Returns None immediately.
        """
        self._worker.generate_chunk.emit(level, vbo_manager, chunk_key, chunk)


class SharedLevelGeometry(QObject):
    """
    A class holding the shared level geometry relating to one level.
    This class must exist on the main thread.
    """

    # Class variables
    _instances_lock = Lock()
    _instances: WeakKeyDictionary[BaseLevel, SharedLevelGeometry] = {}

    # Instance variables
    _level: Callable[[], Optional[BaseLevel]]
    _chunks_lock: Lock
    # Store the chunk data weakly so that it gets automatically deallocated
    _chunks: WeakValueDictionary[ChunkKey, SharedChunkData]

    _chunk_generator: ChunkGenerator
    _vbo_manager: SharedVBOManager

    @classmethod
    def instance(cls, level: BaseLevel) -> SharedLevelGeometry:
        with cls._instances_lock:
            if level not in cls._instances:
                cls._instances[level] = invoke(lambda: SharedLevelGeometry(level))
            return cls._instances[level]

    def __init__(self, level: BaseLevel):
        """To get an instance of this class you should use :classmethod:`instance`"""
        super().__init__()
        self._level = ref(level)
        self._chunks_lock = Lock()
        self._chunks = WeakValueDictionary()

        self._vbo_manager = invoke(SharedVBOManager)
        self._chunk_generator = ChunkGenerator()

        self._resource_pack_container = get_gl_resource_pack_container(level)
        self._resource_pack_container.changed.connect(self._resource_pack_changed)

        QCoreApplication.instance().aboutToQuit.connect(self.deleteLater)

    def get_chunk(self, chunk_key: ChunkKey) -> SharedChunkData:
        """Get the geometry for a chunk."""
        with self._chunks_lock:
            chunk = self._chunks.get(chunk_key)
            if chunk is None:
                dimension, cx, cz = chunk_key
                transform = QMatrix4x4()
                transform.translate(cx * 16, 0, cz * 16)
                chunk = self._chunks[chunk_key] = SharedChunkData(transform)
                self._chunk_generator.generate_chunk(
                    self._level(), self._vbo_manager, chunk_key, chunk
                )
            return chunk

    def _resource_pack_changed(self):
        # The geometry of all loaded chunks needs to be rebuilt.
        with self._chunks_lock:
            for chunk_key, chunk in self._chunks.items():
                self._chunk_generator.generate_chunk(
                    self._level(), self._vbo_manager, chunk_key, chunk
                )


class WidgetChunkData(QObject):
    shared: SharedChunkData
    geometry: Optional[SharedChunkGeometry]
    vao: Optional[QOpenGLVertexArrayObject]

    geometry_changed = Signal()

    def __init__(self, shared: SharedChunkData):
        super().__init__()
        self.shared = shared
        self.geometry = None
        self.vao = None
        self.shared.geometry_changed.connect(self.geometry_changed)


def empty_iterator():
    yield from ()


def get_grid_spiral(
    dimension: Dimension, cx: int, cz: int, r: int
) -> Generator[ChunkKey, None, None]:
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


class ChunkContainer(MutableMapping):
    def __init__(self):
        self._chunks: dict[ChunkKey, WidgetChunkData] = {}
        self._order: list[ChunkKey] = []
        self._x = 0
        self._z = 0

    def set_position(self, cx, cz):
        self._x = cx
        self._z = cz
        self._order = sorted(self._order, key=self._dist)

    def __contains__(self, k: ChunkKey):
        return k in self._chunks

    def _dist(self, k: ChunkKey):
        return -abs(k[1] - self._x) - abs(k[2] - self._z)

    def __setitem__(self, k: ChunkKey, v: WidgetChunkData):
        if k not in self._chunks:
            self._order.insert(
                bisect.bisect_left(self._order, self._dist(k), key=self._dist), k
            )
        self._chunks[k] = v

    def __delitem__(self, v: ChunkKey) -> None:
        del self._chunks[v]
        self._order.remove(v)

    def __getitem__(self, k: ChunkKey) -> WidgetChunkData:
        return self._chunks[k]

    def __len__(self) -> int:
        return len(self._chunks)

    def __iter__(self) -> Iterator[ChunkKey]:
        yield from self._order


class WidgetLevelGeometry(QObject, Drawable):
    """
    A class holding the level geometry data relating to one widget.
    This holds all non-shared data and references to the shared data.
    When this object is deleted it will automatically destroy its own data.

    The methods in this class must only be called from the thread the owner QOpenGLWidget is in.
    """

    _shared: SharedLevelGeometry

    _load_radius: int
    _unload_radius: int
    _dimension: Optional[Dimension]
    _camera_chunk: Optional[tuple[int, int]]
    _chunk_finder: Generator[ChunkKey, None, None]
    _running: bool
    _generation_count: int

    # OpenGL attributes
    _context: Optional[QOpenGLContext]
    _surface: QOffscreenSurface
    _program: Optional[QOpenGLShaderProgram]
    _matrix_location: Optional[int]
    _texture_location: Optional[int]
    _chunks: ChunkContainer
    _pending_chunks: dict[ChunkKey, WidgetChunkData]

    # The geometry has changed and needs repainting.
    geometry_changed = Signal()

    def __init__(self, level: BaseLevel):
        super().__init__()
        self._shared = SharedLevelGeometry.instance(level)

        self._load_radius = 5
        self._unload_radius = 10
        self._dimension = None
        self._camera_chunk = None
        self._chunk_finder = empty_iterator()
        self._running = False
        self._generation_count = 0

        self._context = None
        self._surface = QOffscreenSurface()
        self._surface.create()
        self._program = None
        self._matrix_location = None
        self._texture_location = None
        self._chunks = ChunkContainer()
        self._pending_chunks = {}

        self._queue_chunk.connect(self._process_chunk)

    def initializeGL(self):
        """
        Initialise the opengl state.
        The widget context must be current before calling this.
        This must only be called from the QOpenGLWidget that this instance is associated with.
        """
        context = QOpenGLContext.currentContext()
        if not QOpenGLContext.areSharing(context, QOpenGLContext.globalShareContext()):
            raise RuntimeError(
                "The widget context is not sharing with the global context."
            )

        # Make sure any old data no longer exists.
        self._destroy_gl()
        self._context = context
        self._context.aboutToBeDestroyed.connect(self._destroy_gl)

        # Initialise the shader
        self._program = QOpenGLShaderProgram()
        self._program.addShaderFromSourceCode(
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

        self._program.addShaderFromSourceCode(
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

        self._program.bindAttributeLocation("position", 0)
        self._program.bindAttributeLocation("vTexCoord", 1)
        self._program.bindAttributeLocation("vTexOffset", 2)
        self._program.bindAttributeLocation("vTint", 3)
        self._program.link()
        self._program.bind()
        self._matrix_location = self._program.uniformLocation("transformation_matrix")
        self._texture_location = self._program.uniformLocation("image")
        self._program.release()

    def _destroy_gl(self):
        if (
            self._context is not None
            and isValid(self._context)
            and self._context.isValid()
        ):
            if QOpenGLContext.currentContext() is not self._context:
                # Enable the context if it isn't.
                # Use an offscreen surface because the widget surface may no longer exist.
                if not self._context.makeCurrent(self._surface):
                    raise RuntimeError("Could not make context current.")

            self._clear_chunks_no_context()

        self._program = None
        self._matrix_location = None
        self._texture_location = None
        self._context = None

    def __del__(self):
        self._destroy_gl()
        log.debug("deleted WidgetLevelGeometry")

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

        f = QOpenGLContext.currentContext().functions()
        f.glEnable(GL_DEPTH_TEST)
        f.glDepthFunc(GL_LEQUAL)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        f.glEnable(GL_CULL_FACE)
        f.glCullFace(GL_BACK)

        # Draw the geometry
        self._program.bind()

        # Init the texture
        self._program.setUniformValue1i(self._texture_location, 0)

        transform = projection_matrix * view_matrix
        for chunk_data in self._chunks.values():
            self._program.setUniformValue(
                self._matrix_location, transform * chunk_data.shared.model_transform
            )
            chunk_data.geometry.texture.bind(0)
            chunk_data.vao.bind()
            f.glDrawArrays(GL_TRIANGLES, 0, chunk_data.geometry.vertex_count)
            chunk_data.vao.release()

        self._program.release()

    def start(self):
        """Start chunk generation"""
        self._running = True
        self._update_chunk_finder()

    def stop(self):
        self._running = False

    def _update_chunk_finder(self):
        if self._dimension is None or self._camera_chunk is None:
            empty_iterator()
        else:
            cx, cz = self._camera_chunk
            self._chunk_finder = get_grid_spiral(
                self._dimension, cx, cz, self._load_radius
            )
            self._queue_next_chunk()

    def _clear_chunks(self):
        """Unload all chunk data. It is the job of the caller to handle the chunk generator."""
        if self._context is None:
            return
        if not self._context.makeCurrent(self._surface):
            raise RuntimeError("Could not make context current.")
        self._clear_chunks_no_context()
        self._context.doneCurrent()

    def _clear_chunks_no_context(self):
        """Unload all chunk data. Caller manages the GL context."""
        for chunk in self._chunks.values():
            if isValid(chunk.vao):
                # I don't understand where this is being destroyed from
                chunk.vao.destroy()
        self._context.doneCurrent()
        self._chunks.clear()
        self._pending_chunks.clear()

    def _clear_far_chunks(self):
        """
        Unload all chunk data outside the unload render distance.
        It is the job of the caller to handle the chunk generator.
        """
        if self._context is None:
            return
        if self._camera_chunk is None:
            return

        if not self._context.makeCurrent(self._surface):
            raise RuntimeError("Could not make context current.")

        camera_cx, camera_cz = self._camera_chunk
        min_cx = camera_cx - self._unload_radius
        max_cx = camera_cx + self._unload_radius
        min_cz = camera_cz - self._unload_radius
        max_cz = camera_cz + self._unload_radius

        for container in (self._chunks, self._pending_chunks):
            remove_chunk_keys = []
            for chunk_key, chunk in container.items():
                _, chunk_cx, chunk_cz = chunk_key
                if (
                    chunk_cx < min_cx
                    or chunk_cx > max_cx
                    or chunk_cz < min_cz
                    or chunk_cz > max_cz
                ):
                    if chunk.vao is not None:
                        chunk.vao.destroy()
                    remove_chunk_keys.append(chunk_key)
            for chunk_key in remove_chunk_keys:
                del container[chunk_key]

        self._context.doneCurrent()

    def set_dimension(self, dimension: Dimension):
        if dimension != self._dimension:
            self._dimension = dimension
            self._clear_chunks()
            self._update_chunk_finder()

    def set_location(self, cx: int, cz: int):
        """Set the chunk the camera is in."""
        cx = int(cx)
        cz = int(cz)
        location = (cx, cz)
        if location != self._camera_chunk:
            self._camera_chunk = location
            self._clear_far_chunks()
            self._update_chunk_finder()
            self._chunks.set_position(cx, cz)

    def set_render_distance(self, load_distance: int, unload_distance: int):
        """
        Set the render distance attributes.

        :param load_distance: The radius within which to load chunks.
        :param unload_distance: The radius outside which chunks will be unloaded.
        """
        if unload_distance < load_distance + 2:
            # Make sure that unload distance is larger than load distance plus a margin
            unload_distance = load_distance + 2

        if unload_distance < self._unload_radius:
            # TODO: Unload chunks outside the radius
            raise NotImplementedError

        self._load_radius = load_distance
        self._unload_radius = unload_distance
        self._clear_far_chunks()
        self._update_chunk_finder()

    def _queue_next_chunk(self):
        if self._running and self._generation_count == 0:
            # The instance is running and there are no existing generation calls running.
            self._generation_count += 1
            self._queue_chunk.emit()

    _queue_chunk = Signal()

    def _process_chunk(self):
        """Generate a chunk. This must not be called directly."""
        while True:
            # Find a chunk key to process
            chunk_key = next(self._chunk_finder, None)
            if chunk_key is None:
                self._generation_count -= 1
                return
            elif chunk_key in self._chunks or chunk_key in self._pending_chunks:
                continue
            else:
                break

        shared_chunk_data = self._shared.get_chunk(chunk_key)
        widget_chunk_data = WidgetChunkData(shared_chunk_data)
        shared_geometry = shared_chunk_data.geometry

        def create_vao(chunk: WidgetChunkData):
            if not self._context.makeCurrent(self._surface):
                raise RuntimeError("Could not make context current.")

            f = QOpenGLContext.currentContext().functions()

            if chunk.vao is None:
                # Create the VAO if one does not exist.
                chunk.vao = QOpenGLVertexArrayObject()
                chunk.vao.create()
            chunk.vao.bind()

            # Associate the vbo with the vao
            vbo_container = chunk.shared.geometry
            vbo_container.vbo.bind()

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

            chunk.vao.release()
            vbo_container.vbo.release()

            # Update the vbo attribute.
            # If a VBO was previously stored it will get automatically deleted when the last reference is lost.
            chunk.geometry = vbo_container

            self.geometry_changed.emit()

        if shared_geometry is None:
            # The VBO does not exist yet. on_change will be run when it is loaded
            self._pending_chunks[chunk_key] = widget_chunk_data
            self._generation_count -= 1
        else:
            # vbo already exists
            widget_chunk_data.geometry = shared_geometry
            self._chunks[chunk_key] = widget_chunk_data
            create_vao(widget_chunk_data)
            self._generation_count -= 1
            self._queue_next_chunk()

        def on_change():
            self._generation_count += 1
            if chunk_key in self._pending_chunks:
                self._chunks[chunk_key] = self._pending_chunks.pop(chunk_key)
            if chunk_key in self._chunks:
                create_vao(self._chunks[chunk_key])

            self._generation_count -= 1
            self._queue_next_chunk()

        widget_chunk_data.geometry_changed.connect(on_change)
