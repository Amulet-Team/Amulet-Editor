import errno
import os

import amulet.app


def get_resource_path(*rel_path: str) -> str:
    path = os.path.join(amulet.app.__path__[0], "resource", *rel_path)
    if os.path.exists(path):
        return os.path.realpath(path)
    else:
        raise FileNotFoundError(
            errno.ENOENT, "Could not find resource", os.sep.join(rel_path)
        )
