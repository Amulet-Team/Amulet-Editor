from __future__ import annotations

import collections.abc
import typing

import amulet.core.block
import amulet.resource_pack.mesh.block

__all__ = ["AbstractOpenGLResourcePack"]

class AbstractOpenGLResourcePack:
    def __init__(self) -> None: ...
    def _get_block_model(
        self, arg0: amulet.core.block.BlockStack
    ) -> amulet.resource_pack.mesh.block.BlockMesh:
        """
        abstractmethod to load the BlockMesh. Must be implemented by the subclass.
        """

    def _get_texture_ptr(self) -> int: ...
    def get_block_model(
        self, arg0: amulet.core.block.BlockStack
    ) -> amulet.resource_pack.mesh.block.BlockMesh:
        """
        Get the BlockMesh for the given BlockStack.
        The Block will be translated to the version format using the previously specified translator.
        """

    def get_texture_bounds(self, arg0: str) -> tuple[float, float, float, float]:
        """
        Get the bounding box of a given texture path.
        """

    def get_texture_path(self, arg0: str | None, arg1: str) -> str:
        """
        Get the absolute path of the image from the relative components.
        """

    @property
    def _default_texture_bounds(self) -> tuple[float, float, float, float]: ...
    @_default_texture_bounds.setter
    def _default_texture_bounds(
        self,
        arg0: tuple[
            typing.SupportsFloat,
            typing.SupportsFloat,
            typing.SupportsFloat,
            typing.SupportsFloat,
        ],
    ) -> None: ...
    @property
    def _texture_bounds(self) -> dict[str, tuple[float, float, float, float]]: ...
    @_texture_bounds.setter
    def _texture_bounds(
        self,
        arg0: collections.abc.Mapping[
            str,
            tuple[
                typing.SupportsFloat,
                typing.SupportsFloat,
                typing.SupportsFloat,
                typing.SupportsFloat,
            ],
        ],
    ) -> None: ...
