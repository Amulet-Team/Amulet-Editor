import sys

_fbs_installed = "fbs_runtime" in sys.modules


def fbs_installed():
    return _fbs_installed
