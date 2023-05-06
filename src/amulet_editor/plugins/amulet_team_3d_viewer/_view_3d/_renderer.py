"""PySide6 port of the opengl/hellogl2 example from Qt v5.x"""
# Modified slightly from https://doc.qt.io/qtforpython/examples/example_opengl__hellogl2.html

import ctypes
import math
import numpy
import sys
from PySide6.QtCore import Signal, Qt, QSize, QPointF
from PySide6.QtGui import (QVector3D, QOpenGLFunctions, QMatrix4x4, QOpenGLContext, QSurfaceFormat)
from PySide6.QtOpenGL import (QOpenGLVertexArrayObject, QOpenGLBuffer, QOpenGLShaderProgram, QOpenGLShader)
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from shiboken6 import VoidPtr

from OpenGL import GL


class Window(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self._gl_widget = GLWidget()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self._gl_widget)
        self.setLayout(main_layout)

        self.setWindowTitle(self.tr("Hello GL"))


class Logo:
    def __init__(self):
        self.m_count = 0
        self.i = 0
        self.m_data = numpy.empty(2500 * 6, dtype=ctypes.c_float)

        x1 = +0.06
        y1 = -0.14
        x2 = +0.14
        y2 = -0.06
        x3 = +0.08
        y3 = +0.00
        x4 = +0.30
        y4 = +0.22

        self.quad(x1, y1, x2, y2, y2, x2, y1, x1)
        self.quad(x3, y3, x4, y4, y4, x4, y3, x3)

        self.extrude(x1, y1, x2, y2)
        self.extrude(x2, y2, y2, x2)
        self.extrude(y2, x2, y1, x1)
        self.extrude(y1, x1, x1, y1)
        self.extrude(x3, y3, x4, y4)
        self.extrude(x4, y4, y4, x4)
        self.extrude(y4, x4, y3, x3)

        NUM_SECTORS = 100

        for i in range(NUM_SECTORS):
            angle = (i * 2 * math.pi) / NUM_SECTORS
            x5 = 0.30 * math.sin(angle)
            y5 = 0.30 * math.cos(angle)
            x6 = 0.20 * math.sin(angle)
            y6 = 0.20 * math.cos(angle)

            angle = ((i + 1) * 2 * math.pi) / NUM_SECTORS
            x7 = 0.20 * math.sin(angle)
            y7 = 0.20 * math.cos(angle)
            x8 = 0.30 * math.sin(angle)
            y8 = 0.30 * math.cos(angle)

            self.quad(x5, y5, x6, y6, x7, y7, x8, y8)

            self.extrude(x6, y6, x7, y7)
            self.extrude(x8, y8, x5, y5)

    def const_data(self):
        return self.m_data.tobytes()

    def count(self):
        return self.m_count

    def vertex_count(self):
        return self.m_count / 6

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
        n = QVector3D.normal(QVector3D(x4 - x1, y4 - y1, 0), QVector3D(x2 - x1, y2 - y1, 0))

        self.add(QVector3D(x1, y1, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)

        self.add(QVector3D(x3, y3, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)

        n = QVector3D.normal(QVector3D(x1 - x4, y1 - y4, 0), QVector3D(x2 - x4, y2 - y4, 0))

        self.add(QVector3D(x4, y4, 0.05), n)
        self.add(QVector3D(x1, y1, 0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)

        self.add(QVector3D(x2, y2, 0.05), n)
        self.add(QVector3D(x3, y3, 0.05), n)
        self.add(QVector3D(x4, y4, 0.05), n)

    def extrude(self, x1, y1, x2, y2):
        n = QVector3D.normal(QVector3D(0, 0, -0.1), QVector3D(x2 - x1, y2 - y1, 0))

        self.add(QVector3D(x1, y1, 0.05), n)
        self.add(QVector3D(x1, y1, -0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)

        self.add(QVector3D(x2, y2, -0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)
        self.add(QVector3D(x1, y1, -0.05), n)

    def add(self, v, n):
        self.m_data[self.i] = v.x()
        self.i += 1
        self.m_data[self.i] = v.y()
        self.i += 1
        self.m_data[self.i] = v.z()
        self.i += 1
        self.m_data[self.i] = n.x()
        self.i += 1
        self.m_data[self.i] = n.y()
        self.i += 1
        self.m_data[self.i] = n.z()
        self.i += 1
        self.m_count += 6


class GLWidget(QOpenGLWidget, QOpenGLFunctions):
    x_rotation_changed = Signal(int)
    y_rotation_changed = Signal(int)
    z_rotation_changed = Signal(int)

    def __init__(self, parent=None):
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        fmt.setVersion(2, 0)
        self.setFormat(fmt)

        self._x_rot = 0
        self._y_rot = 0
        self._z_rot = 0
        self._last_pos = QPointF()
        self.logo = Logo()
        self.vao = QOpenGLVertexArrayObject()
        self._logo_vbo = QOpenGLBuffer()
        self.program = QOpenGLShaderProgram()
        self.proj = QMatrix4x4()
        self.camera = QMatrix4x4()
        self.world = QMatrix4x4()

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
        self._logo_vbo.destroy()
        del self.program
        self.program = None
        self.doneCurrent()

    def initializeGL(self):
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.initializeOpenGLFunctions()
        self.glClearColor(0, 0, 0, 1)

        self.program = QOpenGLShaderProgram()

        self._vertex_shader = """#version 110
                                void main()
                                {
                                    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                                }"""

        self._fragment_shader = """#version 110
                                void main()
                                {
                                    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
                                }
                                """

        self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, self._vertex_shader)
        self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, self._fragment_shader)
        self.program.link()

        self.program.bind()

        self.vao.create()
        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao)

        self._logo_vbo.create()
        self._logo_vbo.bind()
        float_size = ctypes.sizeof(ctypes.c_float)
        self._logo_vbo.allocate(self.logo.const_data(), self.logo.count() * float_size)

        self.setup_vertex_attribs()

        self.camera.setToIdentity()
        self.camera.translate(0, 0, -1)

        self.program.release()
        vao_binder = None

    def setup_vertex_attribs(self):
        self._logo_vbo.bind()
        f = QOpenGLContext.currentContext().functions()
        f.glEnableVertexAttribArray(0)
        f.glEnableVertexAttribArray(1)
        float_size = ctypes.sizeof(ctypes.c_float)

        null = VoidPtr(0)
        pointer = VoidPtr(3 * float_size)
        f.glVertexAttribPointer(0, 3, int(GL.GL_FLOAT), int(GL.GL_FALSE), 6 * float_size, null)
        f.glVertexAttribPointer(1, 3, int(GL.GL_FLOAT), int(GL.GL_FALSE), 6 * float_size, pointer)
        self._logo_vbo.release()

    def paintGL(self):
        self.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.glEnable(GL.GL_DEPTH_TEST)
        self.glEnable(GL.GL_CULL_FACE)

        self.world.setToIdentity()
        self.world.rotate(180 - (self._x_rot / 16), 1, 0, 0)
        self.world.rotate(self._y_rot / 16, 0, 1, 0)
        self.world.rotate(self._z_rot / 16, 0, 0, 1)

        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao)
        self.program.bind()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadMatrixf((self.camera * self.world).data())

        self.glDrawArrays(GL.GL_TRIANGLES, 0, self.logo.vertex_count())
        self.program.release()
        vao_binder = None

    def resizeGL(self, width, height):
        self.proj.setToIdentity()
        self.proj.perspective(45, width / height, 0.01, 100)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadMatrixf(self.proj.data())

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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # fmt = QSurfaceFormat()
    # fmt.setDepthBufferSize(24)
    # fmt.setVersion(2, 0)
    # QSurfaceFormat.setDefaultFormat(fmt)

    main_window = Window()
    main_window.resize(main_window.sizeHint())
    main_window.show()

    res = app.exec()
    sys.exit(res)
