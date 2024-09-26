from __future__ import annotations
import logging
from typing import Generator, Callable, Iterator, Any, TypeVar
import ctypes
from threading import Lock
from weakref import WeakKeyDictionary, WeakValueDictionary, ref
from collections.abc import MutableMapping
import bisect
import itertools
import numpy
import numpy.typing

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
from amulet.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.chunk import Chunk
from amulet.chunk_components import BlockComponent
from amulet.selection import SelectionGroup

import thread_manager

from ._drawable import Drawable
from ._resource_pack import (
    OpenGLResourcePack,
    get_gl_resource_pack_container,
)
from amulet_editor.application._invoke import invoke
from amulet_editor.models.widgets.traceback_dialog import CatchException

from ._chunk_builder import create_lod0_chunk

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

FloatSize = ctypes.sizeof(ctypes.c_float)

log = logging.getLogger(__name__)

ChunkKey = tuple[DimensionId, int, int]


class ContextException(RuntimeError):
    pass


class SharedVBOManager(QObject):
    """
    This class manages creating and destroying VBOs so that you don't have to.
    The VBO is created in a context that shares the global share context. Creation is done on the main thread.
    All methods are thread safe.
    """

    _context: QOpenGLContext
    _surface: QOffscreenSurface
    _vbos: set[QOpenGLBuffer]

    def __init__(self) -> None:
        """Use new class method"""
        app_instance = QCoreApplication.instance()
        if app_instance is None:
            raise RuntimeError("Qt App does not exist.")
        if QThread.currentThread() is not app_instance.thread():
            raise RuntimeError(
                "SharedVBOManager must be constructed on the main thread."
            )

        super().__init__()
        context = self._context = QOpenGLContext()
        global_context = QOpenGLContext.globalShareContext()
        if global_context is None:
            raise ContextException("Global OpenGL context does not exist.")
        self._context.setShareContext(global_context)
        self._context.create()

        # Create the surface
        surface = self._surface = QOffscreenSurface()
        self._surface.create()

        lock = self._lock = Lock()
        vbos = self._vbos = set()

        def destroy() -> None:
            with CatchException(), lock:
                if not context.makeCurrent(surface):
                    raise ContextException("Could not make context current.")

                for vbo in vbos:
                    vbo.destroy()
                vbos.clear()

                context.doneCurrent()

        self.destroyed.connect(destroy)

    def create_vbo(self, buffer: bytes) -> QOpenGLBuffer:
        """
        Create a shared VBO.
        There will be no active OpenGL context in the main thread when this is finished.
        """

        def create_vbo() -> QOpenGLBuffer:
            with self._lock:
                if not self._context.makeCurrent(self._surface):
                    raise ContextException("Could not make context current.")

                vbo = QOpenGLBuffer()
                vbo.create()
                vbo.bind()
                vbo.allocate(buffer, len(buffer))
                vbo.release()
                self._vbos.add(vbo)
                self._context.doneCurrent()

                return vbo

        return invoke(create_vbo)

    def destroy_vbo(self, vbo: QOpenGLBuffer) -> None:
        """
        Destroy a shared VBO.
        There will be no active OpenGL context in the main thread when this is finished.
        """
        log.debug("destroy_vbo")

        def destroy_vbo() -> None:
            with self._lock:
                if vbo not in self._vbos:
                    raise RuntimeError(
                        "vbo was not created by this class or has already been destroyed."
                    )

                if not self._context.makeCurrent(self._surface):
                    raise ContextException("Could not make context current.")
                vbo.destroy()
                self._context.doneCurrent()
                log.debug("Destroyed vbo")

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
    geometry: SharedChunkGeometry | None

    # Signals
    # Emitted when the geometry has been modified.
    geometry_changed = Signal()

    def __init__(self, model_transform: QMatrix4x4) -> None:
        super().__init__()
        self.model_transform: QMatrix4x4 = model_transform
        self.geometry = None


class ChunkGeneratorWorker(QObject):
    """
    This object exists in a secondary thread so that chunk generation does not block the main thread.
    The OpenGL calls need to be done on the main thread.
    """

    def __init__(self) -> None:
        super().__init__()
        self.generate_chunk.connect(self._generate_chunk)

    generate_chunk = Signal(object, object, object, object)

    @Slot(object, object, object, object)
    def _generate_chunk(
        self,
        level: Level,
        vbo_manager: SharedVBOManager,
        chunk_key: ChunkKey,
        chunk_data: SharedChunkData,
    ) -> None:
        with CatchException():
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

            dimension_id, cx, cz = chunk_key
            dimension = level.get_dimension(dimension_id)

            buffer = b""
            try:
                chunk = dimension.get_chunk_handle(cx, cz).get([BlockComponent.ComponentID])
            except ChunkDoesNotExist:
                # TODO: Add void geometry
                log.debug(f"Chunk {chunk_key} does not exist")
                buffer = self._get_empty_geometry(
                    dimension.bounds(),
                    resource_pack, cx, cz
                )
            except ChunkLoadError:
                # TODO: Add error geometry
                log.exception(f"Error loading chunk {chunk_key}", exc_info=True)
                buffer = self._get_error_geometry(
                    dimension.bounds(),
                    resource_pack, cx, cz
                )
                # self._create_error_geometry()
            else:
                if isinstance(chunk, BlockComponent):
                    log.debug(f"Creating geometry for chunk {chunk_key}")
                    # chunk_verts, chunk_verts_translucent = create_lod0_chunk(
                    #     resource_pack,
                    #     self._sub_chunks(level, dimension, cx, cz, chunk),
                    #     chunk.block.palette,
                    # )
                    # verts = chunk_verts + chunk_verts_translucent
                    # if verts:
                    #     buffer = numpy.concatenate(verts).tobytes()
                else:
                    log.debug(f"Chunk {chunk_key} does not implement BlockComponent.")

            log.debug(f"Generated array for {chunk_key}")

            vbo = vbo_manager.create_vbo(buffer)

            vertex_count = len(buffer) // (12 * FloatSize)

            chunk_data.geometry = SharedChunkGeometry(vbo, vertex_count, resource_pack)

            def destroy_vbo() -> None:
                with CatchException():
                    vbo_manager.destroy_vbo(vbo)

            # When the container gets garbage collected, destroy the vbo
            chunk_data.geometry.destroyed.connect(destroy_vbo)
            chunk_data.geometry_changed.emit()

            log.debug(f"Generated chunk {chunk_key}")

    def _sub_chunks(
        self, level: Level, dimension: DimensionId, cx: int, cz: int, chunk: Chunk
    ) -> list[tuple[numpy.ndarray, int]]:
        """
        Create sub-chunk arrays that extend into the neighbour sub-chunks by one block.

        :param dimension: The dimension the chunk came from
        :param cx: The chunk x coordinate of the chunk
        :param cz: The chunk z coordinate of the chunk
        :param chunk: The chunk object
        :return: A list of tuples containing the larger block array and the location of the sub-chunk
        """
        if not isinstance(chunk, BlockComponent):
            return []
        sections = chunk.block.sections
        sub_chunks = []
        neighbour_chunks = {}
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            try:
                chunk_handle = level.get_dimension(dimension).get_chunk_handle(
                    cx + dx, cz + dz
                )
                chunk = chunk_handle.get([BlockComponent.ComponentID])
                if isinstance(chunk, BlockComponent):
                    neighbour_chunks[(dx, dz)] = chunk.block
            except ChunkLoadError:
                continue

        for cy, sub_chunk in sections.items():
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
                neighbour_sections = neighbour_blocks.sections
                if cy not in neighbour_sections:
                    continue
                if chunk_offset == (-1, 0):
                    larger_blocks[0, 1:-1, 1:-1] = neighbour_sections[cy][-1, :, :]
                elif chunk_offset == (1, 0):
                    larger_blocks[-1, 1:-1, 1:-1] = neighbour_sections[cy][0, :, :]
                elif chunk_offset == (0, -1):
                    larger_blocks[1:-1, 1:-1, 0] = neighbour_sections[cy][:, :, -1]
                elif chunk_offset == (0, 1):
                    larger_blocks[1:-1, 1:-1, -1] = neighbour_sections[cy][:, :, 0]
            if cy - 1 in sections:
                larger_blocks[1:-1, 0, 1:-1] = sections[cy - 1][:, -1, :]
            if cy + 1 in sections:
                larger_blocks[1:-1, -1, 1:-1] = sections[cy + 1][:, 0, :]
            sub_chunks.append((larger_blocks, cy * 16))
        return sub_chunks

    def _create_chunk_plane(
        self, height: float
    ) -> tuple[numpy.ndarray, numpy.ndarray]:
        box = numpy.array([(0, height, 0), (16, height, 16)])
        _box_coordinates = numpy.array(list(itertools.product(*box.T.tolist())))
        _cube_face_lut = numpy.array(
            [  # This maps to the verticies used (defined in cube_vert_lut)
                0,
                4,
                5,
                1,
                3,
                7,
                6,
                2,
            ]
        )
        box = box.ravel()
        _texture_index = numpy.array([0, 2, 3, 5, 0, 2, 3, 5], numpy.uint32)
        _uv_slice = numpy.array(
            [0, 1, 2, 1, 2, 3, 0, 3] * 2, dtype=numpy.uint32
        ).reshape((-1, 8)) + numpy.arange(0, 8, 4).reshape((-1, 1))

        _tri_face = numpy.array([0, 1, 2, 0, 2, 3] * 2, numpy.uint32).reshape(
            (-1, 6)
        ) + numpy.arange(0, 8, 4).reshape((-1, 1))
        return (
            _box_coordinates[_cube_face_lut[_tri_face]].reshape((-1, 3)),
            box[_texture_index[_uv_slice]]
            .reshape(-1, 2)[_tri_face, :]
            .reshape((-1, 2)),
        )

    def _create_grid(
        self,
        level_bounds: SelectionGroup,
        resource_pack: OpenGLResourcePack,
        texture_namespace: str,
        texture_path: str,
        draw_floor: bool,
        draw_ceil: bool,
        tint: tuple[float, float, float],
    ) -> numpy.typing.NDArray[numpy.float32]:
        vert_len = 12
        plane: numpy.ndarray = numpy.ones(
            (vert_len * 12 * (draw_floor + draw_ceil)),
            dtype=numpy.float32,
        ).reshape((-1, vert_len))
        if draw_floor:
            plane[:12, :3], plane[:12, 3:5] = self._create_chunk_plane(
                level_bounds.min_y - 0.01
            )
            if draw_ceil:
                plane[12:, :3], plane[12:, 3:5] = self._create_chunk_plane(
                    level_bounds.max_y + 0.01
                )
        elif draw_ceil:
            plane[:12, :3], plane[:12, 3:5] = self._create_chunk_plane(
                level_bounds.max_y + 0.01
            )

        plane[:, 5:9] = resource_pack.texture_bounds(
            resource_pack.get_texture_path(texture_namespace, texture_path)
        )
        plane[:, 9:12] = tint
        return plane

    def _get_empty_geometry(
        self,
        level_bounds: SelectionGroup,
        resource_pack: OpenGLResourcePack,
        cx: int,
        cz: int
    ) -> bytes:
        return self._create_grid(
            level_bounds,
            resource_pack,
            "amulet",
            "amulet_ui/chunk_grid_null",
            True,
            True,
            (1, 1, 1) if (cx + cz) % 2 else (0.8, 0.8, 0.8),
        ).ravel().tobytes()

    def _get_error_geometry(
        self,
        level_bounds: SelectionGroup,
        resource_pack: OpenGLResourcePack,
        cx: int,
        cz: int
    ) -> bytes:
        return self._create_grid(
            level_bounds,
            resource_pack,
            "amulet",
            "amulet_ui/chunk_grid_error",
            True,
            True,
            (1, 1, 1) if (cx + cz) % 2 else (0.8, 0.8, 0.8),
        ).ravel().tobytes()


class ChunkGenerator(QObject):
    _thread: QThread
    _worker: ChunkGeneratorWorker

    def __init__(self) -> None:
        super().__init__()
        thread = self._thread = thread_manager.new_thread("ChunkGeneratorThread")
        self._thread.start()
        worker = self._worker = ChunkGeneratorWorker()
        self._worker.moveToThread(self._thread)

        def destroy() -> None:
            with CatchException():
                worker.deleteLater()
                log.debug("Quitting chunk generation thread.")
                thread.quit()

        self.destroyed.connect(destroy)
        app_instance = QCoreApplication.instance()
        if app_instance is None:
            raise RuntimeError("Qt App is None")
        app_instance.aboutToQuit.connect(self.deleteLater)

    def generate_chunk(
        self,
        level: Level,
        vbo_manager: SharedVBOManager,
        chunk_key: ChunkKey,
        chunk: SharedChunkData,
    ) -> None:
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
    _instances = WeakKeyDictionary[Level, "SharedLevelGeometry"]()

    # Instance variables
    _level: Callable[[], Level | None]
    _chunks_lock: Lock
    # Store the chunk data weakly so that it gets automatically deallocated
    _chunks: WeakValueDictionary[ChunkKey, SharedChunkData]

    _chunk_generator: ChunkGenerator
    _vbo_manager: SharedVBOManager

    @classmethod
    def instance(cls, level: Level) -> SharedLevelGeometry:
        with cls._instances_lock:
            if level not in cls._instances:
                cls._instances[level] = invoke(lambda: SharedLevelGeometry(level))
            return cls._instances[level]

    def __init__(self, level: Level) -> None:
        """To get an instance of this class you should use :classmethod:`instance`"""
        super().__init__()
        self._level = ref(level)
        self._chunks_lock = Lock()
        self._chunks = WeakValueDictionary()

        self._vbo_manager = invoke(SharedVBOManager)
        self._chunk_generator = ChunkGenerator()

        self._resource_pack_container = get_gl_resource_pack_container(level)
        self._resource_pack_container.changed.connect(self._resource_pack_changed)

        app_instance = QCoreApplication.instance()
        if app_instance is None:
            raise RuntimeError("Qt App is None")
        app_instance.aboutToQuit.connect(self.deleteLater)

    def _get_level(self) -> Level:
        level = self._level()
        if level is None:
            raise RuntimeError("Level does not exist.")
        return level

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
                    self._get_level(), self._vbo_manager, chunk_key, chunk
                )
            return chunk

    def _resource_pack_changed(self) -> None:
        # The geometry of all loaded chunks needs to be rebuilt.
        with CatchException(), self._chunks_lock:
            for chunk_key, chunk in self._chunks.items():
                self._chunk_generator.generate_chunk(
                    self._get_level(), self._vbo_manager, chunk_key, chunk
                )


class WidgetChunkData(QObject):
    shared: SharedChunkData
    geometry: SharedChunkGeometry | None
    vao: QOpenGLVertexArrayObject | None

    geometry_changed = Signal()

    def __init__(self, shared: SharedChunkData) -> None:
        super().__init__()
        self.shared = shared
        self.geometry = None
        self.vao = None
        self.shared.geometry_changed.connect(self.geometry_changed)

    def __del__(self) -> None:
        if self.vao is not None:
            log.warning("VAO has not been destroyed.")


def empty_iterator() -> Iterator[ChunkKey]:
    yield from ()


def get_grid_spiral(
    dimension: DimensionId, cx: int, cz: int, r: int
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


class ChunkContainer(MutableMapping[ChunkKey, WidgetChunkData]):
    def __init__(self) -> None:
        self._chunks: dict[ChunkKey, WidgetChunkData] = {}
        self._order: list[ChunkKey] = []
        self._x: int = 0
        self._z: int = 0

    def set_position(self, cx: int, cz: int) -> None:
        self._x = cx
        self._z = cz
        self._order = sorted(self._order, key=self._dist)

    def __contains__(self, k: ChunkKey | Any) -> bool:
        return k in self._chunks

    def _dist(self, k: ChunkKey) -> int:
        return -abs(k[1] - self._x) - abs(k[2] - self._z)

    def __setitem__(self, k: ChunkKey, v: WidgetChunkData) -> None:
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


class LevelGeometryGLData:
    context: QOpenGLContext
    program: QOpenGLShaderProgram
    matrix_location: int
    texture_location: int

    def __init__(
        self,
        context: QOpenGLContext,
        program: QOpenGLShaderProgram,
        matrix_location: int,
        texture_location: int,
    ):
        self.context = context
        self.program = program
        self.matrix_location = matrix_location
        self.texture_location = texture_location


class LevelGeometry(QObject, Drawable):
    """
    A class holding the level geometry data relating to one widget.
    This holds all non-shared data and references to the shared data.
    When this object is deleted it will automatically destroy its own data.

    The methods in this class must only be called from the thread the owner QOpenGLWidget is in.
    """

    _shared: SharedLevelGeometry

    _load_radius: int
    _unload_radius: int
    _dimension: DimensionId | None
    _camera_chunk: tuple[int, int] | None
    _chunk_finder: Iterator[ChunkKey]
    _generation_count: int

    # OpenGL attributes
    _surface: QOffscreenSurface
    _gl_data_: LevelGeometryGLData | None
    _chunks: ChunkContainer
    _pending_chunks: dict[ChunkKey, WidgetChunkData]

    # The geometry has changed and needs repainting.
    geometry_changed = Signal()

    def __init__(self, level: Level) -> None:
        log.debug("LevelGeometry.__init__ start")
        super().__init__()
        self._shared = SharedLevelGeometry.instance(level)

        self._load_radius = 5
        self._unload_radius = 10
        self._dimension = None
        self._camera_chunk = None
        self._chunk_finder = empty_iterator()
        self._generation_count = 0

        self._gl_data_ = None
        self._surface = QOffscreenSurface()
        self._surface.create()
        self._chunks = ChunkContainer()
        self._pending_chunks = {}

        self._queue_chunk.connect(self._process_chunk)
        log.debug("LevelGeometry.__init__ end")

    @property
    def _gl_data(self) -> LevelGeometryGLData:
        if self._gl_data_ is None:
            raise RuntimeError("GL state has not been initialised.")
        return self._gl_data_

    def initializeGL(self) -> None:
        """
        Initialise the opengl state.
        The widget context must be current before calling this.
        This must only be called from the QOpenGLWidget that this instance is associated with.
        """
        log.debug("LevelGeometry.initializeGL start")
        context = QOpenGLContext.currentContext()
        if not QOpenGLContext.areSharing(context, QOpenGLContext.globalShareContext()):
            raise ContextException(
                "The widget context is not sharing with the global context."
            )

        if self._gl_data_ is not None:
            raise RuntimeError(
                "This has been initialised before without being destroyed."
            )

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
        texture_location = program.uniformLocation("image")
        program.release()

        self._gl_data_ = LevelGeometryGLData(
            context, program, matrix_location, texture_location
        )
        self._init_geometry_no_context()
        self._update_chunk_finder()
        log.debug("LevelGeometry.initializeGL end")

    def destroyGL(self) -> None:
        """
        Destroy all the data associated with this context.
        Once finished the context may be destroyed.
        initializeGL may be called again to continue using the data.
        The caller must activate the context.
        """
        with CatchException():
            log.debug("LevelGeometry.destroyGL start")
            self._gl_data_ = None
            self._destroy_geometry_no_context()
            log.debug("LevelGeometry.destroyGL end")

    def __del__(self) -> None:
        log.debug("LevelGeometry.__del__")

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        """
        Draw the level.
        The context must be active before calling this.

        :param projection_matrix: The camera internal projection matrix.
        :param view_matrix: The camera external matrix.
        """
        log.debug("LevelGeometry.paintGL start")
        gl_data = self._gl_data_
        if gl_data is None:
            return
        if QOpenGLContext.currentContext() is not gl_data.context:
            raise ContextException("Context is not valid")

        f = QOpenGLContext.currentContext().functions()
        f.glEnable(GL_DEPTH_TEST)
        f.glDepthFunc(GL_LEQUAL)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        f.glEnable(GL_CULL_FACE)
        f.glCullFace(GL_BACK)

        # Draw the geometry
        gl_data.program.bind()

        # Init the texture
        gl_data.program.setUniformValue1i(gl_data.texture_location, 0)

        transform = projection_matrix * view_matrix
        for chunk_data in self._chunks.values():
            gl_data.program.setUniformValue(
                gl_data.matrix_location, transform * chunk_data.shared.model_transform
            )
            geometry = chunk_data.geometry
            vao = chunk_data.vao
            if geometry is None or vao is None:
                raise RuntimeError
            geometry.texture.bind(0)
            vao.bind()
            f.glDrawArrays(GL_TRIANGLES, 0, geometry.vertex_count)
            vao.release()

        gl_data.program.release()
        log.debug("LevelGeometry.paintGL end")

    def _update_chunk_finder(self) -> None:
        if self._dimension is None or self._camera_chunk is None:
            empty_iterator()
        else:
            cx, cz = self._camera_chunk
            self._chunk_finder = get_grid_spiral(
                self._dimension, cx, cz, self._load_radius
            )
            self._queue_next_chunk()

    def _init_geometry_no_context(self) -> None:
        """
        Initialise the OpenGL data for all existing chunk objects.
        This is the opposite of _destroy_vao_no_context
        The caller manages the context.
        """
        for chunk in self._chunks.values():
            # Don't signal that the geometry has changed.
            # Most of the chunks are not valid yet and errors will occur if we try and draw them.
            self._create_vao(chunk, False)

    def _destroy_geometry_no_context(self) -> None:
        """
        Destroy all Vertex Array Objects.
        The VBOs are defined in the shared context so do not need to be destroyed here.
        This leaves the state such that the VAOs can be created again.
        """
        log.debug(f"Clearing {len(self._chunks)} VAOs from chunks")
        for chunk in self._chunks.values():
            if chunk.vao is not None:  # and isValid(chunk.vao):
                # I don't understand where this is being destroyed from
                chunk.vao.destroy()
                chunk.vao = None

        log.debug(f"Clearing {len(self._pending_chunks)} VAOs from pending_chunks")
        for chunk in self._pending_chunks.values():
            if chunk.vao is not None:  # and isValid(chunk.vao):
                # I don't understand where this is being destroyed from
                chunk.vao.destroy()
                chunk.vao = None
        log.debug("cleared VAOs")

    def _clear_chunks_no_context(self) -> None:
        """
        Clears all geometry data.
        The context must be current before calling this.
        """
        self._destroy_geometry_no_context()
        self._chunks.clear()
        self._pending_chunks.clear()

    def _clear_chunks(self) -> None:
        """Unload all chunk data. It is the job of the caller to handle the chunk generator."""
        gl_data = self._gl_data_
        if gl_data is None:
            return
        if not gl_data.context.makeCurrent(self._surface):
            raise ContextException("Could not make context current.")
        self._clear_chunks_no_context()
        gl_data.context.doneCurrent()

    def _clear_far_chunks(self) -> None:
        """
        Unload all chunk data outside the unload render distance.
        It is the job of the caller to handle the chunk generator.
        """
        gl_data = self._gl_data_
        if gl_data is None or self._camera_chunk is None:
            return

        if not gl_data.context.makeCurrent(self._surface):
            raise ContextException("Could not make context current.")

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
                        chunk.vao = None
                    remove_chunk_keys.append(chunk_key)
            for chunk_key in remove_chunk_keys:
                del container[chunk_key]

        gl_data.context.doneCurrent()

    def set_dimension(self, dimension: DimensionId) -> None:
        if dimension != self._dimension:
            self._dimension = dimension
            self._clear_chunks()
            self._update_chunk_finder()

    def set_location(self, cx: int, cz: int) -> None:
        """Set the chunk the camera is in."""
        cx = int(cx)
        cz = int(cz)
        location = (cx, cz)
        if location != self._camera_chunk:
            self._camera_chunk = location
            self._clear_far_chunks()
            self._update_chunk_finder()
            self._chunks.set_position(cx, cz)

    def set_render_distance(self, load_distance: int, unload_distance: int) -> None:
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

    def _queue_next_chunk(self) -> None:
        if self._gl_data_ and self._generation_count == 0:
            # The instance is running and there are no existing generation calls running.
            self._generation_count += 1
            self._queue_chunk.emit()

    _queue_chunk = Signal()

    def _create_vao(self, chunk: WidgetChunkData, signal: bool = True) -> None:
        gl_data = self._gl_data_
        if gl_data is None or not gl_data.context.makeCurrent(self._surface):
            raise ContextException("Could not make context current.")

        f = QOpenGLContext.currentContext().functions()

        if chunk.vao is None:
            # Create the VAO if one does not exist.
            chunk.vao = QOpenGLVertexArrayObject()
            chunk.vao.create()
        chunk.vao.bind()

        # Associate the vbo with the vao
        vbo_container = chunk.shared.geometry
        if vbo_container is None:
            raise RuntimeError
        vbo_container.vbo.bind()

        # vertex coord
        f.glEnableVertexAttribArray(0)
        f.glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12 * FloatSize, VoidPtr(0))
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
        gl_data.context.doneCurrent()

        # Update the vbo attribute.
        # If a VBO was previously stored it will get automatically deleted when the last reference is lost.
        chunk.geometry = vbo_container

        if signal:
            self.geometry_changed.emit()

    def _process_chunk(self) -> None:
        """Generate a chunk. This must not be called directly."""
        with CatchException():
            if self._gl_data_ is None:
                return
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

            if shared_geometry is None:
                # The VBO does not exist yet. on_change will be run when it is loaded
                if chunk_key in self._chunks:
                    log.warning("existing data")
                self._pending_chunks[chunk_key] = widget_chunk_data
                self._generation_count -= 1
            else:
                # vbo already exists
                widget_chunk_data.geometry = shared_geometry
                if chunk_key in self._chunks:
                    log.warning("existing data")
                self._chunks[chunk_key] = widget_chunk_data
                self._create_vao(widget_chunk_data)
                self._generation_count -= 1
                self._queue_next_chunk()

            # on_change cannot strongly reference self otherwise there is a circular reference
            widget_chunk_data.geometry_changed.connect(
                self.get_on_change_callback(ref(self), chunk_key)
            )

    @staticmethod
    def get_on_change_callback(
        weak_self: Callable[[], LevelGeometry | None], chunk_key: ChunkKey
    ) -> Callable[[], None]:
        def on_change() -> None:
            with CatchException():
                self_ = weak_self()
                if self_ is None or self_._gl_data_ is None:
                    return
                self_._generation_count += 1
                if chunk_key in self_._pending_chunks:
                    if chunk_key in self_._chunks:
                        print("existing data")
                    self_._chunks[chunk_key] = self_._pending_chunks.pop(chunk_key)
                if chunk_key in self_._chunks:
                    self_._create_vao(self_._chunks[chunk_key])

                self_._generation_count -= 1
                self_._queue_next_chunk()

        return on_change
