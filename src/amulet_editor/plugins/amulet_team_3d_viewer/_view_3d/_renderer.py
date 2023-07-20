from __future__ import annotations
import logging
from math import sin, cos, radians

from PySide6.QtCore import Qt, QPointF, Slot
from PySide6.QtGui import (
    QOpenGLFunctions,
    QMouseEvent, QShowEvent, QHideEvent, QOffscreenSurface
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_CULL_FACE,
)

from amulet_editor.data.project import get_level

from amulet_team_resource_pack._api import get_resource_pack_container

from ._camera import Camera, Location, Rotation
from ._key_catcher import KeySrc, KeyCatcher
from ._level_geometry import LevelGeometry
from ._resource_pack import get_gl_resource_pack_container

log = logging.getLogger(__name__)


"""
GPU Memory Deallocation
GPU memory must be associated either with the context or the widget.
Widget memory must be destroyed when the widget is destroyed.
    self.destroyed.connect(func)
Context memory must be destroyed when the context is destroyed.
    self.context().aboutToBeDestroyed.connect(func)
    
Note that if you use a method bound to the instance being destroyed IT WILL NOT BE CALLED.
Due to this all references to GPU memory must be stored in a class stored as an attribute
and a method on that instance should be bound to one of the above examples.
"""


class FirstPersonCanvas(QOpenGLWidget, QOpenGLFunctions):
    def __init__(
            self,
            parent=None
    ):
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        self._camera = Camera()
        self.camera.transform_changed.connect(self.update)
        self.camera.location = Location(0, 0, 0)
        self._last_pos = QPointF()

        self._speed = 0.2

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

        self.camera.location_changed.connect(self._on_move)

        level = get_level()
        self._render_level = LevelGeometry(level)
        self._render_level.changed.connect(self.update)
        self._render_level.set_dimension(level.dimensions[0])

        self._resource_pack_container = get_resource_pack_container(level)
        self._resource_pack_container.changing.connect(lambda prom: prom.progress_change.connect(lambda prog: print(f"Loading resource pack {prog}")))
        self._gl_resource_pack_container = get_gl_resource_pack_container(level)
        self._gl_resource_pack_container.changing.connect(lambda prom: prom.progress_change.connect(lambda prog: print(f"Loading GL resource pack {prog}")))
        self._resource_pack_container.init()

    @property
    def camera(self) -> Camera:
        return self._camera

    def showEvent(self, event: QShowEvent) -> None:
        self._render_level.start()

    def hideEvent(self, event: QHideEvent) -> None:
        self._render_level.stop()

    def initializeGL(self):
        """Private initialisation method called by the QOpenGLWidget"""
        log.debug(f"Initialising GL for {self}")

        # Set up the destruction function
        context = self.context()
        destroyed = False

        def destroy_gl():
            # If this was a method it would not get called.
            nonlocal destroyed
            if not destroyed:
                log.debug(f"Destroying GL for {self}")
                context.makeCurrent(QOffscreenSurface())
                self._render_level.destroyGL()
                context.doneCurrent()
                destroyed = True

        context.aboutToBeDestroyed.connect(destroy_gl)
        self.destroyed.connect(destroy_gl)

        self.initializeOpenGLFunctions()
        self.glClearColor(1, 0, 0, 1)
        self._render_level.initializeGL()

    def paintGL(self):
        """Private paint method called by the QOpenGLWidget"""
        self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.glEnable(GL_DEPTH_TEST)
        self.glEnable(GL_CULL_FACE)

        self._render_level.paintGL(self.camera.intrinsic_matrix, self.camera.extrinsic_matrix)

    def resizeGL(self, width, height):
        """Private resize method called by the QOpenGLWidget"""
        self.camera.set_perspective_projection(45, width / height, 0.01, 10_000)

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

    def _on_move(self):
        x, _, z = self.camera.location
        self._render_level.set_location(x // 16, z // 16)

    def _move_relative(self, angle: int):
        x, y, z = self.camera.location
        azimuth = radians(self.camera.rotation.azimuth + angle)
        self.camera.location = Location(
            x - sin(azimuth) * self._speed, y, z + cos(azimuth) * self._speed
        )

    @Slot()
    def _forwards(self):
        self._move_relative(180)

    @Slot()
    def _right(self):
        self._move_relative(270)

    @Slot()
    def _backwards(self):
        self._move_relative(0)

    @Slot()
    def _left(self):
        self._move_relative(90)

    @Slot()
    def _up(self):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y + self._speed, z)

    @Slot()
    def _down(self):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y - self._speed, z)


# TODO: delta time
