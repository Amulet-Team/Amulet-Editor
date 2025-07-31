def _init() -> None:
    import sys

    import PySide6.QtOpenGL

    from ._view_3d import init

    init(sys.modules[__name__])


_init()

from ._widget import View3D
