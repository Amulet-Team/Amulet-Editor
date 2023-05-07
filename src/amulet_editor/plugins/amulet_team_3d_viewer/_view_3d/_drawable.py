from PySide6.QtGui import QMatrix4x4


class Drawable:
    __slots__ = ("__initialised",)

    def __init__(self):
        self.__initialised = False

    def _initializeGL(self):
        """Initialise the OpenGL state."""
        raise NotImplementedError

    def _paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        """Paint the OpenGL data."""
        raise NotImplementedError

    def draw(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        if not self.__initialised:
            self._initializeGL()
            self.__initialised = True
        self._paintGL(projection_matrix, view_matrix)
