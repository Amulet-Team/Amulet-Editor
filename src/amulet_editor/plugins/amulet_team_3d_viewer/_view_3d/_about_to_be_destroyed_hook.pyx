# cython: language_level=3
# distutils: language = c++
# distutils: libraries = Qt6Gui
# distutils: library_dirs = PySide6Lib

from libcpp cimport bool

from PySide6.QtGui import (
    QOpenGLContext as PySide6_QOpenGLContext,
    QOffscreenSurface as PySide6_QOffscreenSurface
)
from shiboken6 import getCppPointer, isValid


"""
Due to some limitations of the PySide6 library, the QOpenGLContext cannot be accessed from python
after its destructor has started. This stores a pointer directly to the C++ object so it can be
accessed and activated during the destructor to clean up resources.

Ideally we would directly target the real header files for that version but I have no idea how to do that.
"""


cdef extern from *:
    """
    class QObject {
        char pad[16];  // This may cause something to break in the future
    };

    class QSurface {
    public:
        bool supportsOpenGL() const;
    };

    class QOffscreenSurface: public QObject, public QSurface {};

    class QOpenGLContext {
    public:
        bool makeCurrent(QSurface *surface);
        void doneCurrent();
    };
    """

    cdef cppclass QObject:
        pass

    cdef cppclass QSurface:
        bool supportsOpenGL() const

    cdef cppclass QOffscreenSurface(QObject, QSurface):
        pass

    cdef cppclass QOpenGLContext:
        bool makeCurrent(QSurface *surface) except +
        void doneCurrent()


cdef class CyQOpenGLContext:
    cdef QOpenGLContext* _context

    def __init__(self, context: PySide6_QOpenGLContext):
        if not isinstance(context, PySide6_QOpenGLContext):
            raise TypeError
        if not isValid(context):
            raise RuntimeError("The C++ context is not valid.")
        cdef size_t ptr = getCppPointer(context)[0]
        self._context = <QOpenGLContext*> ptr

    cpdef bool makeCurrent(self, surface: PySide6_QOffscreenSurface):
        if not isinstance(surface, PySide6_QOffscreenSurface):
            raise TypeError("Surface must be a PySide6_QOffscreenSurface")

        cdef size_t ptr = getCppPointer(surface)[0]
        cdef QOffscreenSurface* surface_p = <QOffscreenSurface*> ptr
        return self._context.makeCurrent(surface_p)

    cpdef void doneCurrent(self):
        self._context.doneCurrent()
