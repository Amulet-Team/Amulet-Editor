from amulet_editor.data.system import _platform


def get_system() -> str:
    return _platform.PLATFORM_NAME


def is_linux() -> bool:
    return _platform.PLATFORM_NAME == "linux"


def is_mac() -> bool:
    return _platform.PLATFORM_NAME == "mac"


def is_windows() -> bool:
    return _platform.PLATFORM_NAME == "windows"


def is_arch() -> bool:
    if is_linux():
        return (
            "arch" in _platform.LINUX_RELEASE["ID"]
            or "arch" in _platform.LINUX_RELEASE["ID_LIKE"]
        )
    else:
        return False


def is_fedora() -> bool:
    if is_linux():
        return (
            "fedora" in _platform.LINUX_RELEASE["ID"]
            or "fedora" in _platform.LINUX_RELEASE["ID_LIKE"]
        )
    else:
        return False


def is_ubuntu() -> bool:
    if is_linux():
        return (
            "ubuntu" in _platform.LINUX_RELEASE["ID"]
            or "ubuntu" in _platform.LINUX_RELEASE["ID_LIKE"]
        )
    else:
        return False
