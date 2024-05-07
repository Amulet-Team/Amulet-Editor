from PyInstaller.utils.hooks import (
    collect_data_files,
    copy_metadata,
    collect_submodules,
)

datas = [
    *collect_data_files("amulet_editor", excludes=["**/*.ui", "**/*.c", "**/*.pyx"]),
    *collect_data_files(
        "builtin_plugins",
        include_py_files=True,
        excludes=["**/*.ui", "**/*.c", "**/*.pyx", "**/*.pyc"],
    ),
    *copy_metadata("amulet_editor", recursive=True),
]

hiddenimports = [
    *collect_submodules("amulet_editor"),
    "PySide6",
    "OpenGL",
]
