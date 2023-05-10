from math import sin, cos, radians

from PySide6.QtCore import Qt, QSize, QPointF, QObject, QEvent, Slot
from PySide6.QtGui import (
    QOpenGLFunctions,
    QSurfaceFormat,
    QKeyEvent,
    QMouseEvent,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_CULL_FACE,
)

from ._logo import DrawableLogo
from ._camera import Camera, Location, Rotation
from ._key_catcher import KeySrc, KeyCatcher


class Canvas30(QOpenGLWidget):
    """A subclass of QOpenGLWidget that initialises the surface format."""

    def __init__(self, parent=None):
        super().__init__(parent)

        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        fmt.setVersion(3, 0)
        self.setFormat(fmt)


class CameraCanvas(Canvas30):
    """An OpenGL 3.0 canvas with basic movement controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera = Camera()
        self.camera.transform_changed.connect(self.update)
        self.camera.location = Location(0, 0, -1)
        self._last_pos = QPointF()

        self._speed = 0.05

        self._key_catcher = KeyCatcher()
        self.installEventFilter(self._key_catcher)
        self._key_catcher.connect_repeating(
            self._forwards, (KeySrc.Keyboard, Qt.Key.Key_W), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._right, (KeySrc.Keyboard, Qt.Key.Key_D), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._backwards, (KeySrc.Keyboard, Qt.Key.Key_S), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._left, (KeySrc.Keyboard, Qt.Key.Key_A), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._up, (KeySrc.Keyboard, Qt.Key.Key_Space), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._down, (KeySrc.Keyboard, Qt.Key.Key_Shift), frozenset(), 10
        )

    @property
    def camera(self) -> Camera:
        return self._camera

    def mousePressEvent(self, event: QMouseEvent):
        self._last_pos = event.position()
        self.setFocus()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        dx = pos.x() - self._last_pos.x()
        dy = pos.y() - self._last_pos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            azimuth, elevation = self.camera.rotation
            azimuth += dx / 8
            elevation += dy / 8
            self.camera.rotation = Rotation(azimuth, elevation)

        self._last_pos = pos

    def _move_relative(self, angle: int):
        x, y, z = self.camera.location
        azimuth = radians(self.camera.rotation.azimuth + angle)
        self.camera.location = Location(
            x - sin(azimuth) * self._speed, y, z + cos(azimuth) * self._speed
        )

    @Slot()
    def _forwards(self):
        self._move_relative(0)

    @Slot()
    def _right(self):
        self._move_relative(90)

    @Slot()
    def _backwards(self):
        self._move_relative(180)

    @Slot()
    def _left(self):
        self._move_relative(270)

    @Slot()
    def _up(self):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y + self._speed, z)

    @Slot()
    def _down(self):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y - self._speed, z)


class GLWidget(CameraCanvas, QOpenGLFunctions):
    def __init__(self, parent=None):
        CameraCanvas.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        self._logo = DrawableLogo()

    def cleanup(self):
        self.makeCurrent()
        self.doneCurrent()

    def initializeGL(self):
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.initializeOpenGLFunctions()
        self.glClearColor(0, 0, 0, 1)

    def paintGL(self):
        self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.glEnable(GL_DEPTH_TEST)
        self.glEnable(GL_CULL_FACE)

        self._logo.draw(self.camera.intrinsic_matrix, self.camera.extrinsic_matrix)

    def resizeGL(self, width, height):
        self.camera.set_perspective_projection(45, width / height, 0.01, 100)
