def _init() -> None:
    import sys

    import PySide6.QtOpenGL
    import amulet.utils
    import amulet.core
    import amulet.game
    import amulet.level
    import amulet.resource_pack

    from ._view_3d import init

    init(sys.modules[__name__])


_init()

from ._widget import View3D
