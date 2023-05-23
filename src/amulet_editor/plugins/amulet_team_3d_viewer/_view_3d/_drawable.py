from abc import ABC, abstractmethod
from threading import Lock
from weakref import WeakSet
from PySide6.QtGui import QMatrix4x4
from PySide6.QtGui import QOpenGLContext


class Drawable(ABC):
    @abstractmethod
    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        raise NotImplementedError


class OpenGLDrawable:
    __slots__ = ("__initialised", "__lock")

    def __init__(self):
        self.__initialised = False
        self.__lock = Lock()

    @abstractmethod
    def _initializeGL(self):
        """Initialise the OpenGL state."""
        raise NotImplementedError

    @abstractmethod
    def _paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        """Paint the OpenGL data."""
        raise NotImplementedError

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        if not self.__initialised:
            with self.__lock:
                if not self.__initialised:
                    self._initializeGL()
                    self.__initialised = True
        self._paintGL(projection_matrix, view_matrix)


class SharedOpenGLDrawable:
    """An OpenGL object shared between multiple contexts."""

    __slots__ = ("__shared_initialised", "__contexts", "__lock")

    def __init__(self):
        self.__shared_initialised = False
        self.__contexts: WeakSet[QOpenGLContext] = WeakSet()
        self.__lock = Lock()

    @abstractmethod
    def _initializeSharedGL(self):
        """Initialise the shared OpenGL state. Shared data like VBOs."""
        raise NotImplementedError

    @abstractmethod
    def _initializeContextGL(self):
        """Initialise the local OpenGL state. Unique data like VAOs."""
        raise NotImplementedError

    @abstractmethod
    def _paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        """Paint the OpenGL data."""
        raise NotImplementedError

    def paintGL(self, projection_matrix: QMatrix4x4, view_matrix: QMatrix4x4):
        if not self.__shared_initialised:
            with self.__lock:
                if not self.__shared_initialised:
                    self._initializeSharedGL()
                    self.__shared_initialised = True
        if QOpenGLContext.currentContext() not in self.__contexts:
            context = QOpenGLContext.currentContext()
            if context is None:
                raise RuntimeError("Drawing cannot happen without a current context.")
            self._initializeContextGL()
            self.__contexts.add(context)
        self._paintGL(projection_matrix, view_matrix)
