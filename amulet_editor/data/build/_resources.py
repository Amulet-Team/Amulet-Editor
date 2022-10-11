import errno
import os

import amulet_editor


def get_resource(*rel_path: str):
    path = os.path.join(amulet_editor.__path__[0], "resources", *rel_path)
    if os.path.exists(path):
        return os.path.realpath(path)
    else:
        raise FileNotFoundError(
            errno.ENOENT, "Could not find resource", os.sep.join(rel_path)
        )
