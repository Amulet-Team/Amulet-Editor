import os

from amulet_editor.data import system


def save_directories() -> list[str]:
    """
    Returns a list of paths to all default Minecraft save
    directories on the current device.
    """

    directories: list[str] = []

    if system.is_windows():
        directories.extend(
            (
                os.path.join(
                    os.getenv("APPDATA"),
                    ".minecraft",
                    "saves",
                ),
                os.path.join(
                    os.getenv("LOCALAPPDATA"),
                    "Packages",
                    "Microsoft.MinecraftUWP_8wekyb3d8bbwe",
                    "LocalState",
                    "games",
                    "com.mojang",
                    "minecraftWorlds",
                ),
            )
        )
    elif system.is_mac():
        directories.extend(
            (
                os.path.join(
                    os.path.expanduser("~"),
                    "Library",
                    "Application Support",
                    "minecraft",
                    "saves",
                ),
            )
        )
    elif system.is_linux():
        directories.extend(
            (
                os.path.join(
                    os.path.expanduser("~"),
                    ".minecraft",
                    "saves",
                ),
            )
        )

    return list(filter(os.path.isdir, directories))
