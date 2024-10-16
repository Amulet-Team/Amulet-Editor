from __future__ import annotations

import amulet.block
import amulet.mesh.block

__all__ = ["AbstractOpenGLResourcePack"]

class AbstractOpenGLResourcePack:
    _default_texture_bounds: tuple[float, float, float, float]
    _texture_bounds: dict[str, tuple[float, float, float, float]]
    def __init__(self) -> None: ...
    def _get_block_model(
        self, arg0: amulet.block.BlockStack
    ) -> amulet.mesh.block.BlockMesh:
        """
        abstractmethod to load the BlockMesh. Must be implemented by the subclass.
        """

    def get_block_model(
        self, arg0: amulet.block.BlockStack
    ) -> amulet.mesh.block.BlockMesh:
        """
        Get the BlockMesh for the given BlockStack.
        The Block will be translated to the version format using the previously specified translator.
        """

    def texture_bounds(self, arg0: str) -> tuple[float, float, float, float]:
        """
        Get the bounding box of a given texture path.
        """
