from __future__ import annotations
from typing import Any, TypeVar
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
from PySide6.QtWidgets import QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.constant import IntConstant
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT as _GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT as _GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST as _GL_DEPTH_TEST,
)

from amulet_editor.data.level import get_level
from amulet_editor.models.widgets.traceback_dialog import CatchException
from amulet_team_resource_pack._api import get_resource_pack_container

from ._camera import Camera, Location, Rotation
from ._key_catcher import KeySrc, KeyCatcher
from ._level_geometry import WidgetLevelGeometry
from ._resource_pack import get_gl_resource_pack_container

log = logging.getLogger(__name__)

T = TypeVar("T")


def dynamic_cast(obj: Any, new_type: type[T]) -> T:
    if not isinstance(obj, new_type):
        raise TypeError(f"{obj} is not an instance of {new_type}")
    return obj


GL_COLOR_BUFFER_BIT = dynamic_cast(_GL_COLOR_BUFFER_BIT, IntConstant)
GL_DEPTH_BUFFER_BIT = dynamic_cast(_GL_DEPTH_BUFFER_BIT, IntConstant)
GL_DEPTH_TEST = dynamic_cast(_GL_DEPTH_TEST, IntConstant)


"""
GPU Memory Deallocation
Context memory must be destroyed when the context is destroyed.
    self.context().aboutToBeDestroyed.connect(func)
    
Note that func must be a python function not a method. If it is a method IT WILL NOT BE CALLED.
I suggest defining a functon in initGL and bind that. Make sure you don't have circular references.
"""


class GlData:
    context_valid: bool
    data_valid: bool
    render_level: WidgetLevelGeometry

    def __init__(self, render_level: WidgetLevelGeometry) -> None:
        self.context_valid = False
        self.data_valid = False
        self.render_level = render_level

    def is_valid(self) -> bool:
        return self.context_valid and self.data_valid

    def init_context(self) -> None:
        if self.context_valid:
            raise RuntimeError("Context was not destroyed.")
        self.context_valid = True

    def destroy_context(self) -> None:
        if not self.context_valid:
            raise RuntimeError("Context was not initialised")
        if self.data_valid:
            raise RuntimeError("Data has not been destroyed.")
        self.context_valid = False

    def init_context_data(self) -> None:
        """
        Initialise the context data.
        The caller is responsible for managing the context.
        """
        if not self.context_valid or self.is_valid():
            # If the context has not been initialised or if it is already full set up then skip
            return
        log.debug("Init context data")
        self.data_valid = True
        self._init_context_data()

    def _init_context_data(self) -> None:
        self.render_level.initializeGL()

    def destroy_context_data(self) -> None:
        """
        Destroy the context data.
        The caller is responsible for managing the context.
        """
        if not self.is_valid():
            return
        self.data_valid = False
        log.debug("Destroying context data")
        self._destroy_context_data()
        log.debug("Destroyed GL")

    def _destroy_context_data(self) -> None:
        self.render_level.destroyGL()

    def __del__(self) -> None:
        with CatchException():
            log.debug("__del__ GlData")
            if self.data_valid:
                raise RuntimeError("Context data was not destroyed.")


class FirstPersonCanvas(QOpenGLWidget, QOpenGLFunctions):
    background_colour = (0.61, 0.70, 0.85)

    _start_pos: QPoint

    # All the OpenGL data owned by this context must be stored in this instance.
    # This allows the destructor to have access to the data without needing a pointer to self.
    # Having a pointer to self would stop self being garbage collected.
    _gl_data: GlData

    def __init__(self, parent: QWidget | None = None) -> None:
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        level = get_level()
        if level is None:
            raise RuntimeError(
                "FirstPersonCanvas cannot be constructed when a level does not exist."
            )
        self._level = level
        self._gl_data = GlData(WidgetLevelGeometry(self._level))
        self._gl_data.render_level.geometry_changed.connect(self.update)

        self._camera = Camera()
        self.camera.transform_changed.connect(self.update)
        self.camera.location_changed.connect(self._on_move)
        self._start_pos = QPoint()
        self._mouse_captured = False

        self._speed = 1.0

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

    def initializeGL(self) -> None:
        """Private initialisation method called by the QOpenGLWidget"""
        # You must only put calls that do not need destructing here.
        # Normal initialisation must go in the showEvent and destruction in the hideEvent
        with CatchException():
            log.debug(f"Initialising GL for {self}")
            gl_data = self._gl_data
            gl_data.init_context()

            def destroy_context() -> None:
                nonlocal gl_data  # This is required for gl_data to be garbage collected
                with CatchException():
                    log.debug("Context aboutToBeDestroyed")
                    gl_data.destroy_context()

            # This doesn't work if bound to a method. It must be a function
            self.context().aboutToBeDestroyed.connect(
                destroy_context, Qt.ConnectionType.DirectConnection
            )

            # Do the initialisation
            self.initializeOpenGLFunctions()
            self.glClearColor(*self.background_colour, 1)
            gl_data.init_context_data()
            # TODO: pull this data from somewhere
            # Set the start position after OpenGL has been initialised
            gl_data.render_level.set_dimension(next(iter(self._level.dimension_ids())))
            self.camera.location = Location(0, 0, 0)

    def __del__(self) -> None:
        log.debug("__del__ FirstPersonCanvas")

    @property
    def camera(self) -> Camera:
        return self._camera

    def showEvent(self, event: QShowEvent) -> None:
        with CatchException():
            log.debug("show")
            self.makeCurrent()
            self._gl_data.init_context_data()
            self.doneCurrent()

    def hideEvent(self, event: QHideEvent) -> None:
        with CatchException():
            log.debug("hide")
            self.makeCurrent()
            self._gl_data.destroy_context_data()
            self.doneCurrent()

    def paintGL(self) -> None:
        """Private paint method called by the QOpenGLWidget"""
        with CatchException():
            if (
                not self._gl_data.is_valid()
                or not self.isVisible()
                or QOpenGLContext.currentContext() is not self.context() is not None
            ):
                # Sometimes paintGL is run before initializeGL or when the window is not visible.
                # Sometimes it is called when the context is not active.
                # If we don't skip these cases it crashes the program.
                return

            self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.glEnable(GL_DEPTH_TEST)

            self._gl_data.render_level.paintGL(
                self.camera.intrinsic_matrix, self.camera.extrinsic_matrix
            )

    def resizeGL(self, width: float, height: float) -> None:
        """Private resize method called by the QOpenGLWidget"""
        self.camera.set_perspective_projection(45, width / height, 0.01, 10_000)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.RightButton:
            self._mouse_captured = True
            self._start_pos = event.globalPosition().toPoint()
            self.setFocus()
            QGuiApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
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

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._mouse_captured:
            self._mouse_captured = False
            QGuiApplication.restoreOverrideCursor()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self._faster()
        else:
            self._slower()

    def _on_move(self) -> None:
        x, _, z = self.camera.location
        self._gl_data.render_level.set_location(int(x // 16), int(z // 16))

    def _move_relative(self, angle: int, dt: float) -> None:
        x, y, z = self.camera.location
        azimuth = radians(self.camera.rotation.azimuth + angle)
        self.camera.location = Location(
            x - sin(azimuth) * self._speed * dt, y, z + cos(azimuth) * self._speed * dt
        )

    @Slot()
    def _forwards(self, dt: float) -> None:
        self._move_relative(180, dt)

    @Slot()
    def _right(self, dt: float) -> None:
        self._move_relative(270, dt)

    @Slot()
    def _backwards(self, dt: float) -> None:
        self._move_relative(0, dt)

    @Slot()
    def _left(self, dt: float) -> None:
        self._move_relative(90, dt)

    @Slot()
    def _up(self, dt: float) -> None:
        x, y, z = self.camera.location
        self.camera.location = Location(x, y + self._speed * dt, z)

    @Slot()
    def _down(self, dt: float) -> None:
        x, y, z = self.camera.location
        self.camera.location = Location(x, y - self._speed * dt, z)

    @Slot()
    def _faster(self) -> None:
        self._speed *= 1.1

    @Slot()
    def _slower(self) -> None:
        self._speed /= 1.1
