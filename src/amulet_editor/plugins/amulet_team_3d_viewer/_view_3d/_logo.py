from typing import Optional
import ctypes
import math
import numpy
from PySide6.QtGui import (
    QVector3D,
    QMatrix4x4,
    QOpenGLContext,
)
from PySide6.QtOpenGL import (
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLShaderProgram,
    QOpenGLShader,
)

from shiboken6 import VoidPtr

from OpenGL.GL import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
)

from ._drawable import Drawable

FloatSize = ctypes.sizeof(ctypes.c_float)
GL_FLOAT_INT = int(GL_FLOAT)
GL_FALSE_INT = int(GL_FALSE)


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

    def vertex_count(self) -> int:
        return self.m_count // 6

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
        n = QVector3D.normal(
            QVector3D(x4 - x1, y4 - y1, 0), QVector3D(x2 - x1, y2 - y1, 0)
        )

        self.add(QVector3D(x1, y1, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)

        self.add(QVector3D(x3, y3, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)

        n = QVector3D.normal(
            QVector3D(x1 - x4, y1 - y4, 0), QVector3D(x2 - x4, y2 - y4, 0)
        )

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


class DrawableLogo(Drawable):
    __slots__ = (
        "_primitive",
        "_program",
        "_vao",
        "_vbo",
        "_model_matrix",
        "_matrix_loc",
    )

    def __init__(self):
        super().__init__()
        self._primitive = Logo()
        self._program: Optional[QOpenGLShaderProgram] = None
        self._vao: Optional[QOpenGLVertexArrayObject] = None
        self._vbo: Optional[QOpenGLBuffer] = None
        self._model_matrix = QMatrix4x4()
        self._matrix_loc: Optional[int] = None

    def _initializeGL(self):
        # Initialise the shader
        self._program = QOpenGLShaderProgram()
        self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex,
            """#version 130
            in vec3 position;

            uniform mat4 transformation_matrix;

            void main() {
               gl_Position = transformation_matrix * vec4(position, 1.0);
            }""",
        )
        self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment,
            """#version 130
            out vec4 fragColor;

            void main() {
               fragColor = vec4(1.0, 1.0, 1.0, 1.0);
            }""",
        )
        self._program.link()

        self._program.bind()
        self._matrix_loc = self._program.uniformLocation("transformation_matrix")

        self._vao = QOpenGLVertexArrayObject()
        self._vao.create()
        self._vao.bind()

        self._vbo = QOpenGLBuffer()
        self._vbo.create()
        self._vbo.bind()
        self._vbo.allocate(
            self._primitive.const_data(), self._primitive.count() * FloatSize
        )

        f = QOpenGLContext.currentContext().functions()
        f.glEnableVertexAttribArray(0)
        f.glEnableVertexAttribArray(1)
        f.glVertexAttribPointer(
            0, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(0)
        )
        f.glVertexAttribPointer(
            1, 3, GL_FLOAT_INT, GL_FALSE_INT, 6 * FloatSize, VoidPtr(3 * FloatSize)
        )
        self._vbo.release()

        self._vao.release()

        self._program.release()

    def _paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        self._vao.bind()
        self._program.bind()
        self._program.setUniformValue(
            self._matrix_loc, projection_matrix * view_matrix * self._model_matrix
        )
        QOpenGLContext.currentContext().functions().glDrawArrays(
            GL_TRIANGLES, 0, self._primitive.vertex_count()
        )
        self._program.release()
        self._vao.release()