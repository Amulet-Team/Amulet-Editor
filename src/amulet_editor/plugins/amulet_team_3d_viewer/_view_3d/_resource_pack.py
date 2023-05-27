from typing import Generator, Tuple, Dict, Optional
import struct
import hashlib
import os
import json
from PIL import Image
import numpy
import glob
import logging
from threading import Lock
from weakref import WeakKeyDictionary
from collections import deque

from PySide6.QtCore import QObject, SignalInstance
from PySide6.QtGui import QOpenGLContext
from OpenGL.GL import (
    GL_TEXTURE_2D,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_TEXTURE_MIN_FILTER,
    GL_NEAREST,
    GL_CLAMP_TO_EDGE,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
)

from minecraft_model_reader.api.resource_pack.base import BaseResourcePackManager
from minecraft_model_reader import BlockMesh
import PyMCTranslate
from amulet.api.block import Block
from amulet.api.level import BaseLevel

from ._textureatlas import create_atlas_iter

from amulet_editor.models.generic._promise import Promise
from amulet_editor.models.generic._singleton_signal import SingletonSignal
from amulet_editor.models.generic._key_lock import KeyLock

from amulet_team_resource_pack._api import get_resource_pack as _get_resource_pack, resource_pack_changed as _resource_pack_changed, init_resource_pack as _init_resource_pack

log = logging.getLogger(__name__)


class OpenGLResourcePack:
    """
    This class will take a minecraft_model_reader resource pack and load the textures into a texture atlas.
    After creating an instance initialise must be called. This may be done in a thread.
    """

    _lock = Lock()
    # The translator to look up the version block
    _translator: PyMCTranslate.Version
    # Loaded block models
    _block_models: Dict[Block, BlockMesh]
    # Texture coordinates
    _texture_bounds: Dict[str, Tuple[float, float, float, float]]

    # Image on CPU
    _image_width: int
    _image_height: int
    _image: Optional[numpy.ndarray]

    # Image on GPU
    _gl_textures: WeakKeyDictionary[QOpenGLContext, int]

    def __init__(
        self, resource_pack: BaseResourcePackManager, translator: PyMCTranslate.Version
    ):
        super().__init__()
        self._lock = Lock()
        self._resource_pack = resource_pack
        self._translator = translator
        self._block_models = {}
        self._texture_bounds = {}
        self._image = None
        self._image_width = 0
        self._image_height = 0
        self._gl_textures = WeakKeyDictionary()

    def initialise(self) -> Generator[float, None, None]:
        """Create the atlas texture."""
        with self._lock:
            if self._image is None:
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
                            os.path.join(glob.escape(pack), "**", "*.*"), recursive=True
                        )
                    ),
                    default=0,
                )

                cache_dir = os.path.join(".", "cache", "resource_pack")
                img_path = os.path.join(cache_dir, f"{cache_id}.png")
                bounds_path = os.path.join(cache_dir, f"{cache_id}.json")
                try:
                    with open(bounds_path) as f:
                        cache_mod_time, bounds = json.load(f)
                    if mod_time != cache_mod_time:
                        raise Exception(
                            "The resource packs have changed since last merging."
                        )
                    atlas = Image.open(img_path)
                except:
                    atlas_iter = create_atlas_iter(
                        self._resource_pack.textures
                    )
                    try:
                        while True:
                            yield next(atlas_iter)
                    except StopIteration as e:
                        (
                            atlas,
                            bounds,
                        ) = e.value
                        os.makedirs(cache_dir, exist_ok=True)
                        atlas.save(img_path)
                        with open(bounds_path, "w") as f:
                            json.dump((mod_time, bounds), f)

                self._image_width, self._image_height = atlas.size
                self._image = numpy.array(atlas, numpy.uint8).ravel()
                self._texture_bounds = bounds

    def get_atlas_id(self) -> int:
        """Get the opengl texture id of the atlas in the current context."""
        context = QOpenGLContext.currentContext()
        if context is None:
            raise RuntimeError("Context must be set before calling this.")
        if context not in self._gl_textures:
            # Ensure the atlas is initialised.
            # This will do nothing if it has already been initialised and will block if it is being initialised.
            deque(self.initialise(), maxlen=0)

            f = context.functions()
            # Create the texture location
            gl_texture = self._gl_textures[context] = f.glGenTextures(1)
            f.glBindTexture(GL_TEXTURE_2D, gl_texture)
            f.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            f.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            f.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            f.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            f.glBindTexture(GL_TEXTURE_2D, gl_texture)
            f.glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                self._image_width,
                self._image_height,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                self._image,
            )
            f.glBindTexture(GL_TEXTURE_2D, 0)
            log.debug(f"Finished setting up texture atlas in OpenGL context {context}")

        return self._gl_textures[context]

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


# Each resource pack is unique to the level
_level_locks = KeyLock()
_resource_packs: WeakKeyDictionary[BaseLevel, OpenGLResourcePack] = WeakKeyDictionary()

_lock = Lock()
_signals: WeakKeyDictionary[BaseLevel, tuple[QObject, SignalInstance]] = WeakKeyDictionary()
_tokens: WeakKeyDictionary[BaseLevel, Optional[object]] = WeakKeyDictionary()


def render_resource_pack_changed(level: BaseLevel) -> SignalInstance:
    """Get a Qt SignalInstance that will be emitted when the resource pack for that level changes."""
    with _lock:
        if level not in _signals:
            _signals[level] = SingletonSignal()
        return _signals.get(level)[1]


def load_render_resource_pack(level: BaseLevel) -> Promise[None]:
    """
    Initialise the render resource pack for the level

    :param level: The level to load the render resource pack for.
    :return: None. render_resource_pack_changed for the level will be emitted when finished.
    """

    token = object()

    with _lock:
        if level not in _tokens:
            _resource_pack_changed(level).connect(lambda: load_render_resource_pack(level))
        _tokens[level] = token

    def func(promise_data: Promise.Data):
        promise = _init_resource_pack(level)
        promise.call_chained(promise_data, 0.0, 0.5)

        resource_pack = _get_resource_pack(level)
        # TODO: modify the resource pack library to expose the desired translator
        translator = level.translation_manager.get_version("java", (999, 0, 0))

        rp = OpenGLResourcePack(resource_pack, translator)
        for progress in rp.initialise():
            if promise_data.is_cancel_requested:
                raise Promise.OperationCanceled()

            if _tokens.get(level) is not token:
                # Abort if a new generation has been started
                return

            promise_data.progress_change.emit(0.5 + progress * 0.5)

        _resource_packs[level] = rp
        render_resource_pack_changed(level).emit()

    return Promise(func)


def has_render_resource_pack(level: BaseLevel) -> bool:
    return _resource_packs.get(level) is not None


def get_render_resource_pack(level: BaseLevel) -> OpenGLResourcePack:
    """
    Get the resource pack for the level.
    Will raise a runtime error if this is called before it is initialised.
    """
    rp = _resource_packs.get(level)
    if rp is None:
        raise RuntimeError("The OpenGLResourcePack for this level has not been loaded yet.")
    return rp
