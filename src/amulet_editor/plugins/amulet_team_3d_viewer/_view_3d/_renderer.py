from __future__ import annotations
import logging
from math import sin, cos, radians

from PySide6.QtCore import Qt, QPoint, Slot
from PySide6.QtGui import (
    QOpenGLFunctions,
    QOpenGLContext,
    QMouseEvent,
    QShowEvent,
    QHideEvent,
    QWheelEvent,
    QCursor,
    QGuiApplication,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
)

from amulet_editor.data.project import get_level
from amulet_editor.models.widgets.traceback_dialog import CatchException
from amulet_team_resource_pack._api import get_resource_pack_container

from ._camera import Camera, Location, Rotation
from ._key_catcher import KeySrc, KeyCatcher
from ._level_geometry import WidgetLevelGeometry
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
    background_colour = (0.61, 0.70, 0.85)

    _start_pos: QPoint

    def __init__(self, parent=None):
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)
        self._initialised = False

        self._level = get_level()

        self._camera = Camera()
        self.camera.transform_changed.connect(self.update)
        self.camera.location_changed.connect(self._on_move)
        self._start_pos = QPoint()
        self._mouse_captured = False

        self._speed = 1

        self._key_catcher = KeyCatcher()
        self.installEventFilter(self._key_catcher)
        self._key_catcher.connect_repeating(
            self._forwards, (KeySrc.Keyboard, Qt.Key.Key_I), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._right, (KeySrc.Keyboard, Qt.Key.Key_L), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._backwards, (KeySrc.Keyboard, Qt.Key.Key_K), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._left, (KeySrc.Keyboard, Qt.Key.Key_J), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._up, (KeySrc.Keyboard, Qt.Key.Key_Space), frozenset(), 10
        )
        self._key_catcher.connect_repeating(
            self._down, (KeySrc.Keyboard, Qt.Key.Key_Semicolon), frozenset(), 10
        )

        self._render_level = WidgetLevelGeometry(self._level)
        self._render_level.geometry_changed.connect(self.update)

        self._resource_pack_container = get_resource_pack_container(self._level)
        self._resource_pack_container.changing.connect(
            lambda prom: prom.progress_change.connect(
                lambda prog: print(f"Loading resource pack {prog}")
            )
        )
        self._gl_resource_pack_container = get_gl_resource_pack_container(self._level)
        self._gl_resource_pack_container.changing.connect(
            lambda prom: prom.progress_change.connect(
                lambda prog: print(f"Loading GL resource pack {prog}")
            )
        )
        self._resource_pack_container.init()

    def initializeGL(self):
        """Private initialisation method called by the QOpenGLWidget"""
        # You must only put calls that do not need destructing here.
        # Normal initialisation must go in the showEvent and destruction in the hideEvent
        with CatchException():
            log.debug(f"Initialising GL for {self}")
            self.initializeOpenGLFunctions()
            self.glClearColor(*self.background_colour, 1)
            self._initialised = True

    def __del__(self):
        log.debug("__del__ FirstPersonCanvas")

    @property
    def camera(self) -> Camera:
        return self._camera

    def showEvent(self, event: QShowEvent) -> None:
        with CatchException():
            log.debug("Showing FirstPersonCanvas")
            self.makeCurrent()

            if not self._initialised or QOpenGLContext.currentContext() is None:
                # This can get run before initializeGL in some cases
                # If we don't skip, it crashes the program.
                return

            self._render_level.initializeGL()
            # TODO: pull this data from somewhere
            # Set the start position after OpenGL has been initialised
            self._render_level.set_dimension(self._level.dimensions[0])
            self.camera.location = Location(0, 0, 0)

            self.doneCurrent()

    def hideEvent(self, event: QHideEvent) -> None:
        with CatchException():
            log.debug("Hiding FirstPersonCanvas")
            self.makeCurrent()

            self._render_level.destroyGL()

            self.doneCurrent()

    def paintGL(self):
        """Private paint method called by the QOpenGLWidget"""
        with CatchException():
            if not self._initialised or not self.isVisible() or QOpenGLContext.currentContext() is not self.context() is not None:
                # Sometimes paintGL is run before initializeGL or when the window is not visible.
                # Sometimes it is called when the context is not active.
                # If we don't skip these cases it crashes the program.
                return

            self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.glEnable(GL_DEPTH_TEST)

            self._render_level.paintGL(
                self.camera.intrinsic_matrix, self.camera.extrinsic_matrix
            )

    def resizeGL(self, width, height):
        """Private resize method called by the QOpenGLWidget"""
        self.camera.set_perspective_projection(45, width / height, 0.01, 10_000)

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.RightButton:
            self._mouse_captured = True
            self._start_pos = event.globalPosition().toPoint()
            self.setFocus()
            QGuiApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.RightButton:
            pos = event.globalPosition().toPoint()
            dx = pos.x() - self._start_pos.x()
            dy = pos.y() - self._start_pos.y()

            azimuth, elevation = self.camera.rotation
            azimuth += dx / 8
            elevation += dy / 8
            self.camera.rotation = Rotation(azimuth, elevation)

            QCursor.setPos(self._start_pos)
            # On some systems setPos does not work. We must reset _start_pos to the new pos
            self._start_pos = QCursor.pos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._mouse_captured:
            self._mouse_captured = False
            QGuiApplication.restoreOverrideCursor()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self._faster()
        else:
            self._slower()

    def _on_move(self):
        x, _, z = self.camera.location
        self._render_level.set_location(x // 16, z // 16)

    def _move_relative(self, angle: int, dt: float):
        x, y, z = self.camera.location
        azimuth = radians(self.camera.rotation.azimuth + angle)
        self.camera.location = Location(
            x - sin(azimuth) * self._speed * dt, y, z + cos(azimuth) * self._speed * dt
        )

    @Slot()
    def _forwards(self, dt: float):
        self._move_relative(180, dt)

    @Slot()
    def _right(self, dt: float):
        self._move_relative(270, dt)

    @Slot()
    def _backwards(self, dt: float):
        self._move_relative(0, dt)

    @Slot()
    def _left(self, dt: float):
        self._move_relative(90, dt)

    @Slot()
    def _up(self, dt: float):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y + self._speed * dt, z)

    @Slot()
    def _down(self, dt: float):
        x, y, z = self.camera.location
        self.camera.location = Location(x, y - self._speed * dt, z)

    @Slot()
    def _faster(self):
        self._speed *= 1.1

    @Slot()
    def _slower(self):
        self._speed /= 1.1
