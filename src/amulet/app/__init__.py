import logging as _logging

from . import _version

__version__ = _version.get_versions()["version"]

# init a default logger
_logging.basicConfig(level=_logging.INFO, format="%(levelname)s - %(message)s")


def _init() -> None:
    import os
    import sys

    if os.environ.get("AMULET_SKIP_COMPILE", None):
        return

    # Import dependencies
    import amulet.leveldb
    import amulet.utils
    import amulet.zlib
    import amulet.nbt
    import amulet.core
    import amulet.resource_pack
    import amulet.game
    import amulet.anvil
    import amulet.level

    from ._amulet_app import init

    init(sys.modules[__name__])


_init()
del _init
