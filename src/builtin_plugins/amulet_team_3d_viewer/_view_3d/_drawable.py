from PySide6.QtGui import QMatrix4x4


class Drawable:
    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        raise NotImplementedError

    def initializeGL(self) -> None:
        """Initialise the OpenGL data."""
        raise NotImplementedError
