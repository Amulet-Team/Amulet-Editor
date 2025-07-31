from __future__ import annotations
from typing import Any, TypeVar, SupportsFloat
import logging
from math import sin, cos, radians

from PySide6.QtCore import Qt, QPoint, Slot, QThread, QThreadPool
from PySide6.QtGui import (
    QOpenGLFunctions,
    QOpenGLContext,
    QMouseEvent,
    QShowEvent,
    QHideEvent,
    QWheelEvent,
    QCursor,
    QGuiApplication,
    QMatrix4x4,
)
from PySide6.QtWidgets import QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.constant import IntConstant
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT as _GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT as _GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST as _GL_DEPTH_TEST,
)

from amulet.app.exception import CatchExceptionDialog
from amulet.utils.task_manager import ProgressManager
from amulet.utils.event import EventToken
from amulet.level.abc.level import Level

from plugin.amulet.resource_pack._api import get_resource_pack_container

from plugin.amulet.main_level import get_main_level

from ._settings import render_settings
from ._camera import Camera, Location, Rotation
from ._key_catcher import KeySrc, KeyCatcher

# from ._level_geometry import LevelGeometry
from .level.level_geometry import LevelGeometry
from .resource_pack import (
    get_gl_resource_pack_container,
    OpenGLResourcePackHandle,
    OpenGLResourcePack,
)

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
Context memory must be destroyed before the context is destroyed.
    self.context().aboutToBeDestroyed.connect(func, Qt.ConnectionType.DirectConnection)
    
Note that func must be a python function not a method. If it is a method IT WILL NOT BE CALLED.
I suggest defining a functon in initGL and bind that. Make sure you don't have circular references.
"""


class CanvasGlData:
    """A container for all canvas OpenGL data."""

    render_level: LevelGeometry
    _gl_resource_pack_handle: OpenGLResourcePackHandle

    def __init__(self, level: Level) -> None:
        self.render_level = LevelGeometry(level)
        self._gl_resource_pack_handle = get_gl_resource_pack_container(level)

    def __del__(self) -> None:
        log.debug("CanvasGlData.__del__")

    def _set_resource_pack(self, resource_pack: OpenGLResourcePack) -> None:
        self.render_level.set_resource_pack(resource_pack)

    def init_gl(self) -> None:
        log.debug("CanvasGlData.init_gl()")
        self.render_level.init_gl()

    def wake(self) -> None:
        log.debug("CanvasGlData.wake()")
        # This breaks if it is bound directly to the pyside method
        self._gl_resource_pack_handle.changed.connect(self._set_resource_pack)
        self.render_level.wake()

    def sleep(self) -> None:
        log.debug("CanvasGlData.sleep()")
        self.render_level.sleep()

    def destroy_gl(self) -> None:
        log.debug("CanvasGlData.destroy_gl()")
        self.render_level.destroy_gl()

    def paint_gl(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        self.render_level.paint_gl(projection_matrix, view_matrix)


class FirstPersonCanvas(QOpenGLWidget, QOpenGLFunctions):
    """An OpenGL canvas implementing basic controls and rendering."""

    background_colour = (0.61, 0.70, 0.85)

    _start_pos: QPoint

    # All the OpenGL data owned by this context must be stored in this instance.
    # This allows the destructor to have access to the data without needing a pointer to self.
    # Having a pointer to self would stop self being garbage collected.
    _canvas_gl_data: CanvasGlData

    def __init__(self, parent: QWidget | None = None) -> None:
        log.debug("FirstPersonCanvas.__init__ start")
        if not QThread.isMainThread():
            raise RuntimeError("FirstPersonCanvas must be constructed in main thread")
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        level = get_main_level()
        if level is None:
            raise RuntimeError(
                "FirstPersonCanvas cannot be constructed when a level does not exist."
            )
        self._level = level
        self._canvas_gl_data = CanvasGlData(self._level)

        self._camera = Camera()
        self.camera.transform_changed.connect(self.update)
        self.camera.location_changed.connect(self._on_move)
        self._start_pos = QPoint()
        self._mouse_captured = False

        self._speed = 1.0

        self._changed_token: EventToken[()] | None = None

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
        self._gl_resource_pack_container = get_gl_resource_pack_container(self._level)
        log.debug("FirstPersonCanvas.__init__ end")

    def initializeGL(self) -> None:
        """Private initialisation method called by the QOpenGLWidget"""
        with CatchExceptionDialog("Error initialising OpenGL."):
            log.debug("FirstPersonCanvas.initializeGL start")

            # Destroy OpenGL data upon context destruction.
            # This does not work if destroy_gl is connected directly to aboutToBeDestroyed and I don't know why.
            gl_data = self._canvas_gl_data

            def on_context_destruction() -> None:
                gl_data.destroy_gl()

            self.context().aboutToBeDestroyed.connect(
                on_context_destruction, Qt.ConnectionType.DirectConnection
            )

            # Do the initialisation
            self.initializeOpenGLFunctions()
            r, g, b = self.background_colour
            self.glClearColor(r, g, b, 1)
            self._canvas_gl_data.init_gl()
            # TODO: pull this data from somewhere
            # Set the start position after OpenGL has been initialised
            # gl_data.render_level.set_dimension(next(iter(self._level.dimension_ids())))
            self._canvas_gl_data.render_level.set_dimension("minecraft:overworld")
            self.camera.location = Location(0, 0, 0)
            log.debug("FirstPersonCanvas.initializeGL end")

    def __del__(self) -> None:
        log.debug("FirstPersonCanvas.__del__")

    @property
    def camera(self) -> Camera:
        return self._camera

    def _load_resource_pack(self) -> None:
        # TODO: connect this to the GUI
        progress_manager = ProgressManager()

        def print_msg(msg: str) -> None:
            log.info(msg)

        def print_progress(progress: SupportsFloat) -> None:
            log.info(str(progress))

        progress_text_token = progress_manager.register_progress_text_callback(
            print_msg
        )
        progress_token = progress_manager.register_progress_callback(print_progress)
        self._gl_resource_pack_container.get_gl_resource_pack(progress_manager)
        progress_manager.unregister_progress_text_callback(progress_text_token)
        progress_manager.unregister_progress_callback(progress_token)

    def showEvent(self, event: QShowEvent) -> None:
        with CatchExceptionDialog("Error showing canvas."):
            log.debug("FirstPersonCanvas.showEvent start")

            # Set attributes. These may have changed while we were sleeping.
            self._canvas_gl_data.render_level.set_render_distance(
                render_settings.chunk_load_distance,
                render_settings.chunk_unload_distance,
            )

            # Repaint every time the geometry changes
            self._changed_token = (
                self._canvas_gl_data.render_level.geometry_changed.connect(self.update)
            )

            self._canvas_gl_data.wake()
            QThreadPool.globalInstance().start(self._load_resource_pack)
            log.debug("FirstPersonCanvas.showEvent end")

    def hideEvent(self, event: QHideEvent) -> None:
        with CatchExceptionDialog("Error hiding canvas."):
            log.debug("FirstPersonCanvas.hideEvent start")

            # Disconnect from the geometry changed event
            self._canvas_gl_data.render_level.geometry_changed.disconnect(self._changed_token)
            self._changed_token = None

            self._canvas_gl_data.sleep()
            log.debug("FirstPersonCanvas.hideEvent end")

    def paintGL(self) -> None:
        """Private paint method called by the QOpenGLWidget"""
        with CatchExceptionDialog("Error rendering OpenGL frame."):
            if (
                not self.isVisible()
                or QOpenGLContext.currentContext() is not self.context() is not None
            ):
                # Sometimes paintGL is run before initializeGL or when the window is not visible.
                # Sometimes it is called when the context is not active.
                # If we don't skip these cases it crashes the program.
                return

            log.debug("paintGL")

            self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.glEnable(GL_DEPTH_TEST)

            self._canvas_gl_data.paint_gl(
                self.camera.intrinsic_matrix, self.camera.extrinsic_matrix
            )

    def resizeGL(self, width: float, height: float) -> None:
        """Private resize method called by the QOpenGLWidget"""
        log.debug("FirstPersonCanvas.resizeGL")
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
        self._canvas_gl_data.render_level.set_location(int(x // 16), int(z // 16))

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
