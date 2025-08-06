from __future__ import annotations

import typing

import amulet.level.abc.level
import amulet.utils.event
import plugin.amulet.view_3d._view_3d.resource_pack.abc
import PySide6.QtGui

__all__ = ["LevelGeometry"]

class LevelGeometry:
    def __init__(self, arg0: amulet.level.abc.level.Level) -> None: ...
    def destroy_gl(self) -> None: ...
    def init_gl(self) -> None: ...
    def paint_gl(
        self, arg0: PySide6.QtGui.QMatrix4x4, arg1: PySide6.QtGui.QMatrix4x4
    ) -> None: ...
    def set_dimension(self, dimension: str) -> None: ...
    def set_location(self, cx: typing.SupportsInt, cz: typing.SupportsInt) -> None: ...
    def set_render_distance(
        self, load_radius: typing.SupportsInt, unload_radius: typing.SupportsInt
    ) -> None: ...
    def set_resource_pack(
        self,
        resource_pack: plugin.amulet.view_3d._view_3d.resource_pack.abc.AbstractOpenGLResourcePack,
    ) -> None: ...
    def sleep(self) -> None: ...
    def wake(self) -> None: ...
    @property
    def geometry_changed(self) -> amulet.utils.event.Event[()]:
        """
        Event emitted when the geometry changes.
        """
