from __future__ import annotations

import traceback
from typing import Any, TypeVar, SupportsFloat
import logging
from math import sin, cos, radians

from PySide6.QtCore import Qt, QPoint, Slot, QThread, QThreadPool, QObject
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
    QResizeEvent,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.constant import IntConstant
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT as _GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT as _GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST as _GL_DEPTH_TEST,
)

from amulet.utils.task_manager import ProgressManager
from amulet.utils.event import EventToken
from amulet.utils.matrix import Matrix4x4
from amulet.level.abc.level import Level

from amulet.app.exception import CatchExceptionDialog, display_exception
from amulet.app.invoke import invoke
from amulet.app.qt.signal import Signal

from plugin.amulet.resource_pack import get_resource_pack_handle

from plugin.amulet.level import get_main_level
from plugin.amulet.camera import get_camera_extrinsics, Location, Rotation

from ._settings import render_settings
from ._camera import Camera
from ._key_catcher import KeySrc, KeyCatcher

from .level.level_geometry import LevelGeometry
from .selection import SelectionGeometry
from .resource_pack import (
    get_gl_resource_pack_handle,
    OpenGLResourcePackHandle,
    OpenGLResourcePack,
)

from plugin.amulet.selection import get_selection_manager, SelectionManager

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


class CanvasGlData(QObject):
    """A container for all canvas OpenGL data."""

    render_level: LevelGeometry
    _selection_handle: SelectionManager
    _render_selection: SelectionGeometry

    _level_change_token: EventToken[()] | None
    _selection_change_token: EventToken[()] | None

    geometry_changed = Signal[()]()

    def __init__(self, level: Level) -> None:
        super().__init__()
        self.render_level = LevelGeometry(level)
        self._selection_handle = get_selection_manager()
        self._render_selection = SelectionGeometry()

        self._level_change_token = None
        self._selection_change_token = None

    def __del__(self) -> None:
        log.debug("CanvasGlData.__del__")

    def set_resource_pack(self, resource_pack: OpenGLResourcePack) -> None:
        self.render_level.set_resource_pack(resource_pack)

    def init_gl(self) -> None:
        log.debug(f"CanvasGlData.init_gl({self})")
        self.render_level.init_gl()
        self._render_selection.init_gl()

    def _update_selection(self) -> None:
        self._render_selection.set_selection(self._selection_handle.get_selection())

    def _update_render_distance(self) -> None:
        self.render_level.set_render_distance(
            render_settings.chunk_load_distance,
            render_settings.chunk_unload_distance,
        )

    def wake(self) -> None:
        log.debug(f"CanvasGlData.wake({self})")

        # Start listening for changes
        render_settings.render_distance_changed.connect(self._update_render_distance)
        self._selection_handle.selection_changed.connect(self._update_selection)

        # Manually update these settings.
        # They may have changed while we were sleeping.
        self._update_selection()
        self._update_render_distance()

        # Listen for geometry changes
        self._level_change_token = self.render_level.geometry_changed.connect(
            self.geometry_changed.emit
        )
        self._selection_change_token = self._render_selection.geometry_changed.connect(
            self.geometry_changed.emit
        )

        # Wake the level
        self.render_level.wake()

    def sleep(self) -> None:
        log.debug(f"CanvasGlData.sleep({self})")

        # Sleep the level
        self.render_level.sleep()

        # Stop listening for changes
        render_settings.render_distance_changed.connect(self._update_render_distance)
        self._selection_handle.selection_changed.disconnect(self._update_selection)

        # Disconnect geometry change events
        self.render_level.geometry_changed.disconnect(self._level_change_token)
        self._level_change_token = None
        self._render_selection.geometry_changed.disconnect(self._selection_change_token)
        self._selection_change_token = None

    def destroy_gl(self) -> None:
        log.debug(f"CanvasGlData.destroy_gl()")
        self.render_level.destroy_gl()
        self._render_selection.destroy_gl()

    def paint_gl(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4) -> None:
        self.render_level.paint_gl(projection_matrix, view_matrix)
        self._render_selection.paint_gl(
            Matrix4x4(projection_matrix), Matrix4x4(view_matrix)
        )


class FirstPersonCanvas(QOpenGLWidget, QOpenGLFunctions):
    """An OpenGL canvas implementing basic controls and rendering."""

    background_colour = (0.61, 0.70, 0.85)

    _start_pos: QPoint

    # All the OpenGL data owned by this context must be stored in this instance.
    # This allows the destructor to have access to the data without needing a pointer to self.
    # Having a pointer to self would stop self being garbage collected.
    _canvas_gl_data: CanvasGlData

    def __init__(self, parent: QWidget | None = None) -> None:
        log.debug("FirstPersonCanvas.__init__()")
        if not QThread.isMainThread():
            raise RuntimeError("FirstPersonCanvas must be constructed in main thread")
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)
        self._initialised = False
        self._errors: set[str] = set()

        level = get_main_level()
        if level is None:
            raise RuntimeError(
                "FirstPersonCanvas cannot be constructed when a level does not exist."
            )
        self._level = level
        self._canvas_gl_data = CanvasGlData(self._level)

        self._camera = Camera(get_camera_extrinsics(Location(0, 80, 0), Rotation(0, 90)))
        self._start_pos = QPoint()
        self._right_clicked = False

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

        self._resource_pack_handle = get_resource_pack_handle(self._level)
        self._gl_resource_pack_handle = get_gl_resource_pack_handle(self._level)
        self._gl_resource_pack: OpenGLResourcePack | None = None

        self._loading_overlay = QWidget(self)
        self._loading_layout = QVBoxLayout(self._loading_overlay)
        self._loading_overlay.hide()
        self._loading_layout.addStretch(1)

        self._loading_text_layout = QHBoxLayout()
        self._loading_layout.addLayout(self._loading_text_layout)
        self._loading_text = QLabel()
        self._loading_text.setStyleSheet("font-size: 50px")
        self._loading_text_layout.addStretch(1)
        self._loading_text_layout.addWidget(self._loading_text)
        self._loading_text_layout.addStretch(1)

        self._loading_bar = QProgressBar()
        self._loading_bar.setStyleSheet("font-size: 30px")
        self._loading_layout.addWidget(self._loading_bar)

        self._loading_layout.addStretch(1)

        log.debug(f"FirstPersonCanvas.__init__({self}) end")

    def initializeGL(self) -> None:
        """Private initialisation method called by the QOpenGLWidget"""
        with CatchExceptionDialog("Error initialising OpenGL."):
            log.debug(f"FirstPersonCanvas.initializeGL({self})")

            # Destroy OpenGL data upon context destruction.
            # This does not work if destroy_gl is connected directly to aboutToBeDestroyed and I don't know why.
            gl_data = self._canvas_gl_data

            def on_context_destruction() -> None:
                log.debug("FirstPersonCanvas.canvas().aboutToBeDestroyed")
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
            self._initialised = True
            log.debug(f"FirstPersonCanvas.initializeGL({self}) end")

    def __del__(self) -> None:
        log.debug("FirstPersonCanvas.__del__")

    @property
    def camera(self) -> Camera:
        return self._camera

    def _load_resource_pack(self) -> None:
        with CatchExceptionDialog("Error loading resource pack."):
            log.debug(f"FirstPersonCanvas._load_resource_pack({self})")
            # TODO: connect this to the GUI
            progress_manager = ProgressManager()

            def print_msg(msg: str) -> None:
                self._progress_text_changed.emit(msg)

            def print_progress(progress: SupportsFloat) -> None:
                self._progress_changed.emit(float(progress))

            progress_text_token = progress_manager.register_progress_text_callback(
                print_msg
            )
            progress_token = progress_manager.register_progress_callback(print_progress)
            try:
                gl_resource_pack = self._gl_resource_pack_handle.get_gl_resource_pack(
                    progress_manager
                )
            except Exception:
                raise
            else:
                if gl_resource_pack is not self._gl_resource_pack:
                    self._gl_resource_pack = gl_resource_pack
                    invoke(
                        lambda: self._canvas_gl_data.set_resource_pack(gl_resource_pack)
                    )
            finally:
                progress_manager.unregister_progress_text_callback(progress_text_token)
                progress_manager.unregister_progress_callback(progress_token)
                self._loading_finished.emit()
                log.debug(f"FirstPersonCanvas._load_resource_pack({self}) end")

    def _show_loading_overlay(self) -> None:
        self._loading_overlay.show()
        self._loading_overlay.move(self.pos())
        self._loading_overlay.resize(self.size())
        self._loading_text.setText("")
        self._loading_bar.setValue(0)

    def _queue_load_resource_pack(self) -> None:
        QThreadPool.globalInstance().start(self._load_resource_pack)

    _progress_changed = Signal[float]()

    def _on_progress_changed(self, progress: float) -> None:
        if not self._loading_overlay.isVisible():
            self._show_loading_overlay()
        self._loading_bar.setValue(int(100 * progress))

    _progress_text_changed = Signal[str]()

    def _on_progress_text_changed(self, text: str) -> None:
        if not self._loading_overlay.isVisible():
            self._show_loading_overlay()
        self._loading_text.setText(text)

    _loading_finished = Signal[()]()

    def _hide_loading_overlay(self) -> None:
        self._loading_overlay.hide()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._loading_overlay.isVisible():
            self._loading_overlay.move(self.pos())
            self._loading_overlay.resize(self.size())

    def showEvent(self, event: QShowEvent) -> None:
        with CatchExceptionDialog("Error showing canvas."):
            log.debug(f"FirstPersonCanvas.showEvent({self})")
            if not self._initialised:
                return

            # Update the chunk load position when the camera moves
            self.camera.location_changed.connect(self._on_move)
            # Repaint when the camera transform changes
            self.camera.transform_changed.connect(self.update)

            # Repaint every time the geometry changes
            self._canvas_gl_data.geometry_changed.connect(self.update)

            # Set the resource pack when it changes
            self._gl_resource_pack_handle.changing.connect(
                self._queue_load_resource_pack
            )

            self._progress_changed.connect(self._on_progress_changed)
            self._progress_text_changed.connect(self._on_progress_text_changed)
            self._loading_finished.connect(self._hide_loading_overlay)

            self._canvas_gl_data.wake()
            self._queue_load_resource_pack()
            log.debug("FirstPersonCanvas.showEvent end")

            self._on_move()
            self.update()

    def hideEvent(self, event: QHideEvent) -> None:
        with CatchExceptionDialog("Error hiding canvas."):
            log.debug(f"FirstPersonCanvas.hideEvent({self})")
            if not self._initialised:
                return

            # Disconnect from camera events
            self.camera.transform_changed.disconnect(self.update)
            self.camera.location_changed.disconnect(self._on_move)

            # Disconnect from the geometry changed event
            self._canvas_gl_data.geometry_changed.disconnect(self.update)

            # Disconnect from resource pack changing event
            self._gl_resource_pack_handle.changing.disconnect(
                self._queue_load_resource_pack
            )

            self._progress_changed.disconnect(self._on_progress_changed)
            self._progress_text_changed.disconnect(self._on_progress_text_changed)
            self._loading_finished.disconnect(self._hide_loading_overlay)

            self._canvas_gl_data.sleep()
            log.debug(f"FirstPersonCanvas.hideEvent({self}) end")

    def paintGL(self) -> None:
        """Private paint method called by the QOpenGLWidget"""
        try:
            if (
                not self._initialised
                or not self.isVisible()
                or QOpenGLContext.currentContext() is not self.context() is not None
            ):
                # Sometimes paintGL is run before initializeGL or when the window is not visible.
                # Sometimes it is called when the context is not active.
                # If we don't skip these cases it crashes the program.
                return

            log.debug(f"FirstPersonCanvas.paintGL({self})")

            self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.glEnable(GL_DEPTH_TEST)

            self._canvas_gl_data.paint_gl(
                self.camera.intrinsic_matrix, self.camera.extrinsic_matrix
            )
        except Exception as e:
            log.exception(e)
            traceback_string = "".join(traceback.format_tb(e.__traceback__))
            if traceback_string not in self._errors:
                self._errors.add(traceback_string)
                display_exception(
                    "Error rendering OpenGL frame.", str(e), traceback_string
                )

    def resizeGL(self, width: float, height: float) -> None:
        """Private resize method called by the QOpenGLWidget"""
        log.debug(f"FirstPersonCanvas.resizeGL({self}, {width}, {height})")
        self.camera.set_perspective_projection(70, width / height, 0.01, 10_000)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._right_clicked and event.buttons() & Qt.MouseButton.RightButton:
            self._right_clicked = True
            self._start_pos = event.globalPosition().toPoint()
            self.setFocus()
            QGuiApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._right_clicked:
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
        if self._right_clicked and not event.buttons() & Qt.MouseButton.RightButton:
            self._right_clicked = False
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
            x - sin(azimuth) * self.camera.speed * dt, y, z + cos(azimuth) * self.camera.speed * dt
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
        self.camera.location = Location(x, y + self.camera.speed * dt, z)

    @Slot()
    def _down(self, dt: float) -> None:
        x, y, z = self.camera.location
        self.camera.location = Location(x, y - self.camera.speed * dt, z)

    @Slot()
    def _faster(self) -> None:
        self.camera.speed *= 1.1

    @Slot()
    def _slower(self) -> None:
        self.camera.speed /= 1.1
