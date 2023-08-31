from PyInstaller.utils.hooks import (
    collect_submodules,
)

hiddenimports = [
    *collect_submodules("OpenGL"),  # On my linux install not everything was included.
]
