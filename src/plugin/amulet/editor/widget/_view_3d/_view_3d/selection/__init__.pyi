from __future__ import annotations

import amulet.core.selection.shape_group
import amulet.utils.event
import amulet.utils.matrix

__all__: list[str] = ["SelectionGeometry"]

class SelectionGeometry:
    """
    A class to maintain the OpenGL state of a selection.
    """

    def __init__(self) -> None: ...
    def destroy_gl(self) -> None:
        """
        Destroy the OpenGL state.
        This must be called with the same active OpenGL context used when init_gl was called.
        """

    def init_gl(self) -> None:
        """
        Initialise the OpenGL state.
        This must be called with an active OpenGL context.
        """

    def paint_gl(
        self,
        projection_matrix: amulet.utils.matrix.Matrix4x4,
        view_matrix: amulet.utils.matrix.Matrix4x4,
    ) -> None:
        """
        Paint the selection.
        This must be called with the same active OpenGL context used when init_gl was called.
        """

    def set_selection(
        self, selection_group: amulet.core.selection.shape_group.SelectionShapeGroup
    ) -> None:
        """
        Set the new selection shape group.
        This is thread safe.
        """

    @property
    def geometry_changed(self) -> amulet.utils.event.Event[()]: ...
