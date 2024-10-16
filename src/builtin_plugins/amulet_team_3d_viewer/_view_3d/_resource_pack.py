from typing import Optional
import struct
import hashlib
import os
import json
import glob
import logging
from threading import Lock, RLock
from weakref import WeakKeyDictionary, ref

from PIL import Image
from PIL.ImageQt import ImageQt

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QOpenGLContext, QOffscreenSurface
from PySide6.QtOpenGL import QOpenGLTexture

from amulet.version import VersionNumber
from amulet.block import Block, BlockStack
from amulet.level.abc import Level, DiskLevel
from amulet.game.abc import GameVersion
from amulet.game import get_game_version
from amulet.mesh.block import BlockMesh
from amulet.mesh.block import get_missing_block
from amulet.resource_pack.abc import BaseResourcePackManager

from ._textureatlas import create_atlas

from amulet_editor.application._invoke import invoke
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.models.generic._promise import Promise
from amulet_editor.data.paths._application import cache_directory

from amulet_team_resource_pack._api import get_resource_pack_container
from ._resource_pack_base import AbstractOpenGLResourcePack

log = logging.getLogger(__name__)


class OpenGLResourcePack(AbstractOpenGLResourcePack):
    """
    This class will take a resource pack and load the textures into a texture atlas.
    After creating an instance, initialise must be called.

    """

    _lock = Lock()
    _resource_pack: BaseResourcePackManager
    # The translator to look up the version block
    _game_version: GameVersion

    # Image on GPU
    _texture: Optional[QOpenGLTexture]
    _context: Optional[QOpenGLContext]
    _surface: Optional[QOffscreenSurface]

    def __init__(self, resource_pack: BaseResourcePackManager, translator: GameVersion):
        super().__init__()
        self._lock = Lock()
        self._resource_pack = resource_pack
        self._game_version = translator
        self._texture = None
        self._context = None
        self._surface = None

    def __del__(self) -> None:
        if (
            self._context is not None
            and self._surface is not None
            and self._texture is not None
        ):
            self._context.makeCurrent(self._surface)
            self._texture.destroy()
            self._context.doneCurrent()

    def initialise(self) -> Promise[None]:
        """
        Create the atlas texture.
        """

        def func(promise_data: Promise.Data) -> None:
            with self._lock:
                if self._texture is None:
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
                            raise Exception(
                                "The resource packs have changed since last merging."
                            )
                        _atlas = QImage(img_path)
                    except Exception:
                        (
                            atlas,
                            bounds,
                        ) = create_atlas(
                            self._resource_pack.textures
                        ).call_chained(promise_data)

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
                        self._context = QOpenGLContext()
                        self._context.setShareContext(
                            QOpenGLContext.globalShareContext()
                        )
                        self._context.create()
                        self._surface = QOffscreenSurface()
                        self._surface.create()
                        if not self._context.makeCurrent(self._surface):
                            raise RuntimeError("Could not make context current.")

                        self._texture = QOpenGLTexture(QOpenGLTexture.Target.Target2D)
                        self._texture.setMinificationFilter(
                            QOpenGLTexture.Filter.Nearest
                        )
                        self._texture.setMagnificationFilter(
                            QOpenGLTexture.Filter.Nearest
                        )
                        self._texture.setWrapMode(
                            QOpenGLTexture.CoordinateDirection.DirectionS,
                            QOpenGLTexture.WrapMode.ClampToEdge,
                        )
                        self._texture.setWrapMode(
                            QOpenGLTexture.CoordinateDirection.DirectionT,
                            QOpenGLTexture.WrapMode.ClampToEdge,
                        )
                        self._texture.setData(_atlas)
                        self._texture.create()

                        self._context.doneCurrent()

                    invoke(init_gl)

        return Promise(func)

    def get_texture(self) -> QOpenGLTexture:
        """
        Get the opengl texture for the atlas.
        The GPU data will be destroyed when the last reference to this instance is released.
        :return: A QOpenGLTexture instance.
        """
        with self._lock:
            if self._texture is None:
                raise RuntimeError("The OpenGLResourcePack has not been initialised.")
            return self._texture

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
            return get_missing_block(self._resource_pack)


class OpenGLResourcePackHandle(QObject):
    # Emitted with a promise object when a resource pack change is started.
    changing = Signal(object)  # Promise[None]
    # Emitted when the resource pack has changed.
    changed = Signal()

    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = ref[Level](level)
        self._lock = RLock()
        self._resource_pack: Optional[OpenGLResourcePack] = None
        self._loader: Optional[Promise[None]] = None
        self._resource_pack_container = get_resource_pack_container(level)
        self._resource_pack_container.changed.connect(self._reload)

    @property
    def loader(self) -> Optional[Promise[None]]:
        return self._loader

    @property
    def loaded(self) -> bool:
        """Is there a valid resource pack."""
        return self._resource_pack is not None

    @property
    def resource_pack(self) -> OpenGLResourcePack:
        rp = self._resource_pack
        if rp is None:
            raise RuntimeError(
                "The OpenGLResourcePack for this level has not been loaded yet."
            )
        return rp

    def _reload(self) -> None:
        def func(promise_data: Promise.Data) -> None:
            with self._lock, DisplayException(
                "Error initialising the OpenGL resource pack."
            ):
                level = self._level()
                if level is None:
                    raise Exception("Level is None")
                if isinstance(level, DiskLevel):
                    log.debug(f"Loading OpenGL resource pack for level {level.path}")
                else:
                    log.debug(f"Loading OpenGL resource pack.")
                resource_pack = self._resource_pack_container.resource_pack
                # TODO: modify the resource pack library to expose the desired translator
                translator = get_game_version("java", VersionNumber(2, -1, 0))

                rp = OpenGLResourcePack(resource_pack, translator)
                promise = rp.initialise()
                # TODO: support canceling
                promise.call_chained(promise_data)
                # for progress in rp.initialise():
                #     if promise_data.is_cancel_requested or _tokens.get(level) is not token:
                #         # Abort if a new generation has been started
                #         raise Promise.OperationCanceled()
                #
                #     promise_data.progress_change.emit(0.5 + progress * 0.5)

                self._resource_pack = rp
                self.changed.emit()
                log.debug(f"Loaded OpenGL resource pack for level {level}")

        promise_ = Promise(func)
        old_loader = self._loader
        if old_loader is not None:
            old_loader.cancel()
        self._loader = promise_
        self.changing.emit(promise_)
        promise_.start()


_lock = Lock()
_level_data: WeakKeyDictionary[Level, OpenGLResourcePackHandle] = WeakKeyDictionary()


def get_gl_resource_pack_container(level: Level) -> OpenGLResourcePackHandle:
    with _lock:
        if level not in _level_data:
            _level_data[level] = invoke(lambda: OpenGLResourcePackHandle(level))
        return _level_data[level]
