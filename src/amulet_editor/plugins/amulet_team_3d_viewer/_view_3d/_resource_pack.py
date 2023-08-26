from typing import Tuple, Dict, Optional
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

from minecraft_model_reader.api.resource_pack.base import BaseResourcePackManager
from minecraft_model_reader import BlockMesh
import PyMCTranslate
from amulet.api.block import Block
from amulet.api.level import BaseLevel

from ._textureatlas import create_atlas

from amulet_editor.application._invoke import invoke
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.models.generic._promise import Promise
from amulet_editor.data.paths._application import cache_directory

from amulet_team_resource_pack._api import get_resource_pack_container

log = logging.getLogger(__name__)


class OpenGLResourcePack:
    """
    This class will take a minecraft_model_reader resource pack and load the textures into a texture atlas.
    After creating an instance, initialise must be called.

    """

    _lock = Lock()
    _resource_pack: BaseResourcePackManager
    # The translator to look up the version block
    _translator: PyMCTranslate.Version
    # Loaded block models
    _block_models: Dict[Block, BlockMesh]
    # Texture coordinates
    _texture_bounds: Dict[str, Tuple[float, float, float, float]]

    # Image on GPU
    _texture: Optional[QOpenGLTexture]
    _context: Optional[QOpenGLContext]
    _surface: Optional[QOffscreenSurface]

    def __init__(
        self, resource_pack: BaseResourcePackManager, translator: PyMCTranslate.Version
    ):
        self._lock = Lock()
        self._resource_pack = resource_pack
        self._translator = translator
        self._block_models = {}
        self._texture_bounds = {}
        self._texture = None
        self._context = None
        self._surface = None

    def __del__(self):
        if self._texture is not None:
            self._context.makeCurrent(self._surface)
            self._texture.destroy()
            self._context.doneCurrent()

    def initialise(self) -> Promise[None]:
        """
        Create the atlas texture.
        """

        def func(promise_data: Promise.Data):
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

                    def init_gl():
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

    def get_texture_path(self, namespace: Optional[str], relative_path: str):
        """Get the absolute path of the image from the relative components.
        Useful for getting the id of textures for hard coded textures not connected to a resource pack.
        """
        return self._resource_pack.get_texture_path(namespace, relative_path)

    def texture_bounds(self, texture_path: str) -> Tuple[float, float, float, float]:
        """Get the bounding box of a given texture path."""
        if texture_path in self._texture_bounds:
            return self._texture_bounds[texture_path]
        else:
            return self._texture_bounds[self._resource_pack.missing_no]

    def get_block_model(self, universal_block: Block) -> BlockMesh:
        """Get the BlockMesh class for a given universal Block.
        The Block will be translated to the version format using the
        previously specified translator."""
        if universal_block not in self._block_models:
            version_block = self._translator.block.from_universal(
                universal_block.base_block
            )[0]
            if universal_block.extra_blocks:
                for block_ in universal_block.extra_blocks:
                    version_block += self._translator.block.from_universal(block_)[0]

            self._block_models[universal_block] = self._resource_pack.get_block_model(
                version_block
            )

        return self._block_models[universal_block]


class RenderResourcePackContainer(QObject):
    # Emitted with a promise object when a resource pack change is started.
    changing = Signal(object)  # Promise[None]
    # Emitted when the resource pack has changed.
    changed = Signal()

    def __init__(self, level: BaseLevel):
        super().__init__()
        self._level = ref(level)
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

    def _reload(self):
        def func(promise_data: Promise.Data):
            with self._lock, DisplayException(
                "Error initialising the OpenGL resource pack."
            ):
                level: BaseLevel = self._level()
                log.debug(f"Loading OpenGL resource pack for level {level.level_path}")
                resource_pack = self._resource_pack_container.resource_pack
                # TODO: modify the resource pack library to expose the desired translator
                translator = level.translation_manager.get_version("java", (999, 0, 0))

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
_level_data: WeakKeyDictionary[
    BaseLevel, RenderResourcePackContainer
] = WeakKeyDictionary()


def get_gl_resource_pack_container(level: BaseLevel) -> RenderResourcePackContainer:
    with _lock:
        if level not in _level_data:
            _level_data[level] = invoke(lambda: RenderResourcePackContainer(level))
        return _level_data[level]
