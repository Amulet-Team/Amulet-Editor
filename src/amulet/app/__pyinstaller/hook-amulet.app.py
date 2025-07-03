from PyInstaller.utils.hooks import (
    collect_data_files,
    copy_metadata,
    collect_submodules,
)

datas = [
    *collect_data_files("amulet.app", excludes=["**/*.ui", "**/*.cpp", "**/*.pyc"]),
    *collect_data_files(
        "builtin_plugins",
        include_py_files=True,
        excludes=["**/*.ui", "**/*.cpp", "**/*.pyc"],
    ),
    *copy_metadata("amulet.app", recursive=True),
]

hiddenimports = [
    *collect_submodules("amulet.app"),
    "PySide6",
    "OpenGL",
]
