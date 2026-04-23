if __name__ != "test_amulet_app":
    raise RuntimeError(
        f"Module name is incorrect. Expected: 'test_amulet_app' got '{__name__}'"
    )


import faulthandler as _faulthandler

_faulthandler.enable()
