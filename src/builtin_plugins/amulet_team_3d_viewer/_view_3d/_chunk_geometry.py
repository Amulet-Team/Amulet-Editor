from threading import RLock
from PySide6.QtGui import QMatrix4x4
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLTexture, QOpenGLVertexArrayObject

from amulet.level.abc import ChunkHandle
from amulet.utils.weakref import CallableWeakMethod
from ._resource_pack import OpenGLResourcePack


class ChunkGLData:
    """Class storing all the OpenGL data for a chunk mesh."""

    _resource_pack: OpenGLResourcePack
    texture: QOpenGLTexture
    vbo: QOpenGLBuffer
    vertex_count: int
    vao: QOpenGLVertexArrayObject

    def __init__(
        self,
        resource_pack: OpenGLResourcePack,
        vbo: QOpenGLBuffer,
        vertex_count: int,
        vao: QOpenGLVertexArrayObject,
    ):
        super().__init__()
        self._resource_pack = resource_pack
        self.texture = self._resource_pack.get_texture()
        self.vbo = vbo
        self.vertex_count = vertex_count
        self.vao = vao


class ChunkData:
    # Constant data
    # The chunk handle. Used to get notified when the chunk changed.
    chunk_handle: ChunkHandle
    # The world transform of the data.
    model_transform: QMatrix4x4

    # The OpenGL data.
    geometry: ChunkGLData | None

    def __init__(self, chunk_handle: ChunkHandle, transform: QMatrix4x4) -> None:
        self.chunk_handle = chunk_handle
        self.model_transform = transform

        self._lock = RLock()
        # This will get incremented each time the chunk is changed.
        self.chunk_state: int = 0
        # None if geometry has not been generated or object if it has.
        # If chunk and mesh tokens are the same then the mesher does not need to be run.
        self.geometry_state: int = -1
        self.geometry = None

        # Schedule meshing when the chunk changes.
        self._on_chunk_change = CallableWeakMethod(self.mark_changed)
        self.chunk_handle.changed.connect(self._on_chunk_change)

    def __del__(self) -> None:
        self.chunk_handle.changed.disconnect(self._on_chunk_change)

    def has_changed(self) -> bool:
        """Does the geometry need rebuilding."""
        return self.chunk_state != self.geometry_state

    def mark_changed(self) -> None:
        """Mark the chunk as needing meshing."""
        with self._lock:
            self.chunk_state += 1

    def set_geometry(
        self, geometry_state: int, geometry: ChunkGLData
    ) -> ChunkGLData | None:
        """
        Set the geometry and update the geometry state.
        Returns the old geometry data. The caller must destroy this.
        Only one thread must be allowed to call this at once.
        """
        old_geometry = self.geometry
        self.geometry = geometry
        self.geometry_state = geometry_state
        return old_geometry
