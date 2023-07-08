# This is based on the original Qt3DWindow C++ code with modifications to make it a QWidget.
# Some inspiration is taken from Florian Blume's qt3d-widget

# This code is released under all licences that the original code is licenced under
# At the time of writing this is
# LGPL 3 and GPL 3 (as per https://www.qt.io/product/features)
# BSD-3-Clause (as per the original source code)

# Original copyright
# Copyright (C) 2016 Klaralvdalens Datakonsult AB (KDAB).
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from typing import overload, Optional
import ctypes

import numpy

from OpenGL.GL import (
    GL_FLOAT,
    GL_FALSE,
    GL_BLEND,
    GL_MULTISAMPLE,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_TEXTURE_2D,
    GL_TRIANGLE_FAN,
)

from shiboken6 import VoidPtr
from PySide6.QtCore import QSize
from PySide6.QtGui import QShowEvent, QSurfaceFormat, QOffscreenSurface, QOpenGLContext
from PySide6.QtOpenGL import QOpenGLVertexArrayObject, QOpenGLShader, QOpenGLShaderProgram, QOpenGLBuffer
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from PySide6.Qt3DRender import Qt3DRender
from PySide6.Qt3DInput import Qt3DInput
from PySide6.Qt3DLogic import Qt3DLogic
from PySide6.QtWidgets import QWidget
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras

FloatSize = ctypes.sizeof(ctypes.c_float)


class Qt3DWidget(QOpenGLWidget):
    """
    This is a widget implementation of the Qt3DWindow.
    Qt3DWindow can be turned into a widget with QWidget.createWindowContainer but this does not allow anything to display on top.
    This is a native widget implemented using QOpenGLWidget which allows widgets to be drawn on top.
    Qt 3D is modified to draw into a GPU texture which is then drawn onto the QOpenGLWidget.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # Opengl variables
        self._shader_program: Optional[QOpenGLShaderProgram] = None
        self._vao: Optional[QOpenGLVertexArrayObject] = None
        self._vbo: Optional[QOpenGLBuffer] = None

        # root variables
        self._root = Qt3DCore.QEntity()
        self._user_root: Optional[Qt3DCore.QEntity] = None

        # Frame graph
        self._active_frame_graph: Optional[Qt3DRender.QFrameGraphNode] = None

        # Has the widget been initialised before
        self._initialised = False

        self._aspect_engine = Qt3DCore.QAspectEngine()

        self._render_aspect = Qt3DRender.QRenderAspect()
        self._aspect_engine.registerAspect(self._render_aspect)

        self._input_aspect = Qt3DInput.QInputAspect()
        self._aspect_engine.registerAspect(self._input_aspect)

        self._logic_aspect = Qt3DLogic.QLogicAspect()
        self._aspect_engine.registerAspect(self._logic_aspect)

        # The opengl surface format
        surface_format = QSurfaceFormat.defaultFormat()

        # A component that runs an event each time a frame is drawn by the 3D engine.
        self._frame_action = Qt3DLogic.QFrameAction()

        # Enable mouse events when no mouse button is clicked
        self.setMouseTracking(True)

        # Create a colour texture.
        self._colour_texture = Qt3DRender.QTexture2D()
        self._colour_texture.setSize(self.width(), self.height())
        self._colour_texture.setFormat(Qt3DRender.QAbstractTexture.TextureFormat.RGB8_UNorm)
        self._colour_texture.setMinificationFilter(Qt3DRender.QAbstractTexture.Filter.Linear)
        self._colour_texture.setMagnificationFilter(Qt3DRender.QAbstractTexture.Filter.Linear)
        self._colour_texture.setSamples(surface_format.samples())

        # Setup colour output and connect to the colour texture
        self._colour_output = Qt3DRender.QRenderTargetOutput()
        self._colour_output.setAttachmentPoint(Qt3DRender.QRenderTargetOutput.AttachmentPoint.Color0)
        self._colour_output.setTexture(self._colour_texture)

        # Create depth texture
        self._depth_texture = Qt3DRender.QTexture2D()
        self._depth_texture.setSize(self.width(), self.height())
        self._depth_texture.setFormat(Qt3DRender.QAbstractTexture.TextureFormat.DepthFormat)
        self._depth_texture.setMinificationFilter(Qt3DRender.QAbstractTexture.Filter.Linear)
        self._depth_texture.setMagnificationFilter(Qt3DRender.QAbstractTexture.Filter.Linear)
        self._depth_texture.setComparisonFunction(Qt3DRender.QAbstractTexture.ComparisonFunction.CompareLessEqual)
        self._depth_texture.setComparisonMode(Qt3DRender.QAbstractTexture.ComparisonMode.CompareRefToTexture)
        self._depth_texture.setSamples(surface_format.samples())

        # Setup depth output and connect to the depth texture
        self._depth_output = Qt3DRender.QRenderTargetOutput()
        self._depth_output.setAttachmentPoint(Qt3DRender.QRenderTargetOutput.AttachmentPoint.Depth)
        self._depth_output.setTexture(self._depth_texture)

        # Enable depth testing
        self._depth_test = Qt3DRender.QDepthTest()
        self._depth_test.setDepthFunction(Qt3DRender.QDepthTest.DepthFunction.LessOrEqual)

        # Enable multisampling
        self._multisample_antialiasing = Qt3DRender.QMultiSampleAntiAliasing()

        # Connect them to the render state
        self._render_state_set = Qt3DRender.QRenderStateSet()
        self._render_state_set.addRenderState(self._depth_test)
        self._render_state_set.addRenderState(self._multisample_antialiasing)

        # Initialise the render settings
        self._render_settings = Qt3DRender.QRenderSettings()
        self._render_settings.setActiveFrameGraph(self._render_state_set)

        # Set up the target to render into. We are not drawing to the screen so a custom target is required.
        self._render_target = Qt3DRender.QRenderTarget()
        self._render_target.addOutput(self._colour_output)
        self._render_target.addOutput(self._depth_output)

        # Point the renderer to the target to draw on
        self._render_target_selector = Qt3DRender.QRenderTargetSelector()
        self._render_target_selector.setParent(self._render_state_set)
        self._render_target_selector.setTarget(self._render_target)

        # An offscreen surface to draw to instead of the actual screen.
        self._offscreen_surface = QOffscreenSurface()
        self._offscreen_surface.setFormat(surface_format)
        self._offscreen_surface.create()

        # Point the renderer to the surface to draw on
        self._render_surface_selector = Qt3DRender.QRenderSurfaceSelector()
        self._render_surface_selector.setParent(self._render_target_selector)
        self._render_surface_selector.setSurface(self._offscreen_surface)

        # The camera
        self._camera = Qt3DRender.QCamera()
        self._camera.setParent(self._render_surface_selector)

        # The renderer
        self._forward_renderer = Qt3DExtras.QForwardRenderer()
        self._forward_renderer.setSurface(self._offscreen_surface)
        self._forward_renderer.setCamera(self._camera)
        self.setActiveFrameGraph(self._forward_renderer)

        # Input settings
        self._input_settings = Qt3DInput.QInputSettings()
        self._input_settings.setEventSource(self)

    def initializeGL(self):
        self._vao = QOpenGLVertexArrayObject()
        self._vao.create()

        self._vao.bind()

        self._vbo = QOpenGLBuffer()
        self._vbo.create()
        self._vbo.bind()
        buf = numpy.array([
            0, 0,
            0, 1,
            1, 1,
            1, 0,
        ], dtype=numpy.float32).tobytes()
        self._vbo.allocate(buf, len(buf))

        self._vbo.bind()
        f = QOpenGLContext.currentContext().functions()
        f.glEnableVertexAttribArray(0)
        f.glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * FloatSize, VoidPtr(0))
        self._vbo.release()

        self._vao.release()

        self._shader_program = QOpenGLShaderProgram()
        self._shader_program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex,
            """#version 130

            in vec2 vertex;

            out vec2 texture_coord;

            void main(void) {
                gl_Position = vec4(vertex * 2 - 1, 0.0, 1.0);
                texture_coord = vertex;
            }"""
        )
        self._shader_program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment,
            """#version 130

            in vec2 texture_coord;
            uniform sampler2D image;

            out vec4 frag_colour;

            void main(void) {
                frag_colour = texture(
                    image,
                    texture_coord
                );
            }"""
        )

        self._shader_program.link()

    @overload
    def registerAspect(self, aspect: Qt3DCore.QAbstractAspect):
        ...

    @overload
    def registerAspect(self, aspect: str):
        ...

    def registerAspect(self, aspect):
        """Registers the specified aspect."""
        assert not self.isVisible()
        self._aspect_engine.registerAspect(aspect)

    def setRootEntity(self, root: Optional[Qt3DCore.QEntity]):
        """Sets the specified root entity of the scene."""
        if self._user_root != root:
            if self._user_root is not None:
                self._user_root.setParent(None)
            if root is not None:
                root.setParent(self._root)
            self._user_root = root

    def setActiveFrameGraph(self, activeFrameGraph: Qt3DRender.QFrameGraphNode):
        """Activates the specified activeFrameGraph."""
        if self._active_frame_graph is not None:
            self._active_frame_graph.setParent(None)
        self._active_frame_graph = activeFrameGraph
        self._active_frame_graph.setParent(self._render_surface_selector)

    def activeFrameGraph(self) -> Qt3DRender.QFrameGraphNode:
        """Returns the node of the active frame graph."""
        return self._active_frame_graph

    def defaultFrameGraph(self) -> Qt3DExtras.QForwardRenderer:
        """Returns the node of the default framegraph"""
        return self._forward_renderer

    def camera(self) -> Qt3DRender.QCamera:
        return self._camera

    def renderSettings(self) -> Qt3DRender.QRenderSettings:
        """Returns the render settings of the 3D Window."""
        return self._render_settings

    def showEvent(self, e: QShowEvent):
        """Manages the display events specified in e."""
        if not self._initialised:
            self._root.addComponent(self._render_settings)
            self._root.addComponent(self._input_settings)
            self._root.addComponent(self._frame_action)
            self._frame_action.triggered.connect(self.update)

            self._initialised = True

        self._aspect_engine.setRootEntity(Qt3DCore.QEntityPtr(self._root))
        super().showEvent(e)

    def hideEvent(self, *args, **kwargs) -> None:
        # Disable the render loop before hiding
        self._aspect_engine.setRootEntity(Qt3DCore.QEntityPtr())
        super().hideEvent(*args, **kwargs)

    def paintGL(self):
        f = QOpenGLContext.currentContext().functions()
        f.glClearColor(1.0, 1.0, 1.0, 1.0)
        f.glDisable(GL_BLEND)
        f.glEnable(GL_MULTISAMPLE)
        f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self._shader_program.bind()

        self._vao.bind()
        try:
            if self._colour_texture.status() == Qt3DRender.QAbstractTexture.Status.Ready:
                f.glBindTexture(GL_TEXTURE_2D, self._colour_texture.handle())
                f.glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        finally:
            self._vao.release()

        self._shader_program.release()

    def resizeGL(self, w: int, h: int):
        self._camera.setAspectRatio(w / h)
        # Multiplying the size by 2 gives better results
        self._colour_texture.setSize(w * 2, h * 2)
        self._depth_texture.setSize(w * 2, h * 2)
        self._render_surface_selector.setExternalRenderTargetSize(QSize(w * 2, h * 2))
