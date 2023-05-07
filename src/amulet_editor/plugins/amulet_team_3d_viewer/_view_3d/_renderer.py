from typing import Optional
import ctypes
import math
import numpy
from PySide6.QtCore import Signal, Qt, QSize, QPointF
from PySide6.QtGui import (
    QVector3D,
    QOpenGLFunctions,
    QMatrix4x4,
    QOpenGLContext,
    QSurfaceFormat,
)
from PySide6.QtOpenGL import (
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLShaderProgram,
    QOpenGLShader,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_CULL_FACE,
)

from ._logo import DrawableLogo

class GLWidget(QOpenGLWidget, QOpenGLFunctions):
    x_rotation_changed = Signal(int)
    y_rotation_changed = Signal(int)
    z_rotation_changed = Signal(int)

    def __init__(self, parent=None):
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        fmt.setVersion(3, 0)
        self.setFormat(fmt)

        self._x_rot = 0
        self._y_rot = 0
        self._z_rot = 0
        self._last_pos = QPointF()
        self._logo = DrawableLogo()
        self._projection_matrix = QMatrix4x4()
        self._view_matrix = QMatrix4x4()

    def x_rotation(self):
        return self._x_rot

    def y_rotation(self):
        return self._y_rot

    def z_rotation(self):
        return self._z_rot

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def normalize_angle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def set_xrotation(self, angle):
        angle = self.normalize_angle(angle)
        if angle != self._x_rot:
            self._x_rot = angle
            self.x_rotation_changed.emit(angle)
            self.update()

    def set_yrotation(self, angle):
        angle = self.normalize_angle(angle)
        if angle != self._y_rot:
            self._y_rot = angle
            self.y_rotation_changed.emit(angle)
            self.update()

    def set_zrotation(self, angle):
        angle = self.normalize_angle(angle)
        if angle != self._z_rot:
            self._z_rot = angle
            self.z_rotation_changed.emit(angle)
            self.update()

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

        self._view_matrix.setToIdentity()
        self._view_matrix.translate(0, 0, -1)
        self._view_matrix.rotate(180 - (self._x_rot / 16), 1, 0, 0)
        self._view_matrix.rotate(self._y_rot / 16, 0, 1, 0)
        self._view_matrix.rotate(self._z_rot / 16, 0, 0, 1)

        self._logo.draw(self._projection_matrix, self._view_matrix)

    def resizeGL(self, width, height):
        self._projection_matrix.setToIdentity()
        self._projection_matrix.perspective(45, width / height, 0.01, 100)

    def mousePressEvent(self, event):
        self._last_pos = event.position()

    def mouseMoveEvent(self, event):
        pos = event.position()
        dx = pos.x() - self._last_pos.x()
        dy = pos.y() - self._last_pos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.set_xrotation(self._x_rot - 8 * dy)
            self.set_yrotation(self._y_rot - 8 * dx)

        self._last_pos = pos
