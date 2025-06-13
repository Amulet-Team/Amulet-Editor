from ._widget import View3D


def _init() -> None:
    import sys

    from ._view_3d import init

    init(sys.modules[__name__])


_init()
