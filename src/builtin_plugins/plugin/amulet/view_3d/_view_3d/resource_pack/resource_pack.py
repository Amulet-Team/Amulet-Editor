from typing import Optional
import struct
import hashlib
import os
import json
import glob
import logging
from threading import Lock, Condition
from weakref import WeakKeyDictionary, ref
import traceback

from PIL import Image
from PIL.ImageQt import ImageQt

from shiboken6 import getCppPointer, wrapInstance
from PySide6.QtCore import QObject, Signal, QThreadPool, Qt
from PySide6.QtGui import QImage, QOpenGLContext, QOffscreenSurface
from PySide6.QtOpenGL import QOpenGLTexture

from amulet.utils.cast import dynamic_cast
from amulet.utils.task_manager import (
    AbstractProgressManager,
    VoidProgressManager,
)
from amulet.core.version import VersionNumber
from amulet.core.block import Block, BlockStack
from amulet.level.abc import Level, DiskLevel
from amulet.game.abc import GameVersion
from amulet.game import get_game_version
from amulet.resource_pack.mesh.block import BlockMesh
from amulet.resource_pack.abc import BaseResourcePackManager

from ._textureatlas import create_atlas

from amulet.app.invoke import invoke
from amulet.app.exception import display_exception
from amulet.app.path import cache_directory

from plugin.amulet.resource_pack._api import get_resource_pack_container
from .abc import AbstractOpenGLResourcePack

log = logging.getLogger(__name__)


class ResourcePackGLData:
    # Image on GPU
    texture: QOpenGLTexture
    context: QOpenGLContext
    context_ptr: int

    def __init__(
        self,
        texture: QOpenGLTexture,
        context: QOpenGLContext,
    ):
        self.texture = texture
        self.context = context
        self.context_ptr = getCppPointer(context)[0]


class OpenGLResourcePack(AbstractOpenGLResourcePack):
    """
    This class will take a resource pack and load the textures into a texture atlas.
    """

    _lock = Lock()
    _resource_pack: BaseResourcePackManager
    # The translator to look up the version block
    _game_version: GameVersion

    _gl_data: ResourcePackGLData

    def __init__(
        self,
        resource_pack: BaseResourcePackManager,
        translator: GameVersion,
        progress_manager: AbstractProgressManager = VoidProgressManager(),
    ):
        super().__init__()
        self._lock = Lock()
        self._resource_pack = resource_pack
        self._game_version = translator

        cache_id = struct.unpack(
            "H",
            hashlib.sha1(
                "".join(self._resource_pack.pack_paths).encode("utf-8")
            ).digest()[:2],
        )[0]

        atlas: Image.Image

        if not self._resource_pack.pack_paths:
            log.warning("There are no resource packs to load.")

        mod_time = max(
            (
                os.stat(path).st_mtime
                for pack in self._resource_pack.pack_paths
                for path in glob.glob(
                    os.path.join(glob.escape(pack), "**", "*.*"),
                    recursive=True,
                )
            ),
            default=0,
        )

        cache_dir = os.path.join(cache_directory(), "resource_pack")
        img_path = os.path.join(cache_dir, f"{cache_id}.png")
        bounds_path = os.path.join(cache_dir, f"{cache_id}.json")
        try:
            with open(bounds_path) as f:
                cache_mod_time, bounds = json.load(f)
            if mod_time != cache_mod_time:
                raise Exception("The resource packs have changed since last merging.")
            _atlas = QImage(img_path)
        except Exception:
            (
                atlas,
                bounds,
            ) = create_atlas(self._resource_pack.textures, progress_manager)

            os.makedirs(cache_dir, exist_ok=True)
            atlas.save(img_path)
            with open(bounds_path, "w") as f:
                json.dump((mod_time, bounds), f)
            _atlas = ImageQt(atlas)

        self._texture_bounds = bounds
        self._default_texture_bounds = self._texture_bounds[
            self._resource_pack.missing_no
        ]

        def init_gl() -> None:
            log.debug("Initialising OpenGL resource pack texture.")
            context = QOpenGLContext()
            context.setShareContext(QOpenGLContext.globalShareContext())
            context.create()
            surface = QOffscreenSurface()
            surface.create()
            if not context.makeCurrent(surface):
                raise RuntimeError("Could not make context current.")

            texture = QOpenGLTexture(QOpenGLTexture.Target.Target2D)
            texture.setMinificationFilter(QOpenGLTexture.Filter.Nearest)
            texture.setMagnificationFilter(QOpenGLTexture.Filter.Nearest)
            texture.setWrapMode(
                QOpenGLTexture.CoordinateDirection.DirectionS,
                QOpenGLTexture.WrapMode.ClampToEdge,
            )
            texture.setWrapMode(
                QOpenGLTexture.CoordinateDirection.DirectionT,
                QOpenGLTexture.WrapMode.ClampToEdge,
            )
            texture.setData(_atlas)
            texture.create()

            context.doneCurrent()
            surface.destroy()
            self._gl_data = ResourcePackGLData(
                texture,
                context,
            )
            log.debug("Finished initialising OpenGL resource pack texture.")

        invoke(init_gl)

        gl_data = self._gl_data

        def destroy_gl() -> None:
            if not gl_data.texture.isCreated():
                # Texture was not created or has already been destroyed.
                return
            log.debug("Destroying OpenGL resource pack texture.")
            context = dynamic_cast(
                wrapInstance(gl_data.context_ptr, QOpenGLContext), QOpenGLContext
            )
            surface = QOffscreenSurface()
            surface.create()
            if not context.makeCurrent(surface):
                raise RuntimeError("Could not make context current.")
            gl_data.texture.destroy()
            context.doneCurrent()
            surface.destroy()

        self._gl_data.context.aboutToBeDestroyed.connect(
            destroy_gl, Qt.ConnectionType.DirectConnection
        )

    def __del__(self) -> None:
        log.debug("OpenGLResourcePack.__del__")

    def get_texture(self) -> QOpenGLTexture:
        """
        Get the opengl texture for the atlas.
        The GPU data will be destroyed when the last reference to this instance is released.
        :return: A QOpenGLTexture instance.
        """
        return self._gl_data.texture

    def _get_texture_ptr(self) -> int:
        return getCppPointer(self.get_texture())[0]

    def get_texture_path(self, namespace: Optional[str], relative_path: str) -> str:
        """Get the absolute path of the image from the relative components.
        Useful for getting the id of textures for hard coded textures not connected to a resource pack.
        """
        return self._resource_pack.get_texture_path(namespace, relative_path)

    def _get_block_model(self, block_stack: BlockStack) -> BlockMesh:
        blocks = list[Block]()
        for block in block_stack:
            if self._game_version.supports_version(block.platform, block.version):
                blocks.append(block)
            else:
                # Translate to the required format.
                converted_block, _, _ = get_game_version(
                    block.platform, block.version
                ).block.translate(
                    self._game_version.platform,
                    self._game_version.max_version,
                    block,
                )
                if isinstance(converted_block, Block):
                    blocks.append(converted_block)
        if blocks:
            return self._resource_pack.get_block_model(BlockStack(*blocks))
        else:
            return self._resource_pack.missing_block


class OpenGLResourcePackHandle(QObject):
    # Emitted when the underlying resource pack has changed and a call to get_gl_resource_pack is required.
    changing = Signal()
    # Emitted when the resource pack has changed.
    changed = Signal(OpenGLResourcePack)

    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = ref[Level](level)
        self._condition = Condition(Lock())

        self._resource_pack_container = get_resource_pack_container(level)
        self._gl_resource_pack: OpenGLResourcePack | None = None
        self._load_progress_manager: AbstractProgressManager | None = None

        self._resource_pack_container.changed.connect(self._resource_pack_changed)

    def get_gl_resource_pack(
        self,
        progress_manager: AbstractProgressManager = VoidProgressManager(),
    ) -> OpenGLResourcePack:
        with self._condition:
            if self._load_progress_manager is not None:
                # The resource pack is being loaded by another call.
                # Connect the progress managers
                progress_token = self._load_progress_manager.register_progress_callback(
                    progress_manager.update_progress
                )
                progress_text_token = (
                    self._load_progress_manager.register_progress_text_callback(
                        progress_manager.update_progress_text
                    )
                )

                # Wait until the first call completes. Note that it may fail.
                while self._load_progress_manager is not None:
                    self._condition.wait()

                self._load_progress_manager.unregister_progress_callback(progress_token)
                self._load_progress_manager.unregister_progress_text_callback(
                    progress_text_token
                )

            if self._gl_resource_pack is None:
                # The resource pack has not been loaded
                self._load_progress_manager = progress_manager
            else:
                # The resource pack has already been set/loaded
                return self._gl_resource_pack

        try:
            level = self._level()
            if level is None:
                raise Exception("Level is None")
            if isinstance(level, DiskLevel):
                log.debug(f"Loading OpenGL resource pack for level {level.path}")
            else:
                log.debug(f"Loading OpenGL resource pack.")
            resource_pack = self._resource_pack_container.get_resource_pack(
                progress_manager
            )
            # TODO: modify the resource pack library to expose the desired translator
            translator = get_game_version("java", VersionNumber(2, -1, 0))

            # TODO: support canceling
            gl_resource_pack = OpenGLResourcePack(
                resource_pack, translator, progress_manager
            )
        except Exception as e:
            # Loading failed
            display_exception(
                title="Error initialising the OpenGL resource pack.",
                error=str(e),
                traceback=traceback.format_exc(),
            )
            with self._condition:
                self._load_progress_manager = None
                self._condition.notify_all()
            # re-raise the exception
            raise
        else:
            # Loading succeeded
            with self._condition:
                self._load_progress_manager = None
                self._gl_resource_pack = gl_resource_pack
                self._condition.notify_all()
            log.debug(f"Loaded OpenGL resource pack for level {level}")
            self.changed.emit(gl_resource_pack)
            return self._gl_resource_pack

    def _resource_pack_changed(self) -> None:
        def _reset_and_notify() -> None:
            with self._condition:
                # Wait until the first call completes. Note that it may fail.
                # TODO: support canceling so we don't need to wait
                while self._load_progress_manager is not None:
                    self._condition.wait()
                # Invalidate the previous resource pack
                self._gl_resource_pack = None

            # Notify listeners that the underlying resource pack has changed.
            # A call to get_gl_resource_pack is required to get the new opengl resource pack.
            self.changing.emit()

        QThreadPool.globalInstance().start(_reset_and_notify)


_lock = Lock()
_level_data: WeakKeyDictionary[Level, ref[OpenGLResourcePackHandle]] = (
    WeakKeyDictionary()
)


def get_gl_resource_pack_container(level: Level) -> OpenGLResourcePackHandle:
    """
    Get a handle to the OpenGL resource pack for this level.
    The caller must store a strong reference to this object.
    """
    with _lock:
        handle = _level_data.get(level, lambda: None)()
        if handle is None:
            handle = invoke(lambda: OpenGLResourcePackHandle(level))
            _level_data[level] = ref(handle)
        return handle
