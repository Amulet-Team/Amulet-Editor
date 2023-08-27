try:
    from PyInstaller.utils.hooks import (
        collect_data_files,
        copy_metadata,
        collect_submodules,
    )
except ImportError as e:
    raise ImportError(
        "This is part of the build pipeline. It cannot be imported at runtime."
    ) from e

datas = [
    *collect_data_files("PySide6", includes=["*.pyi", "py.typed"]),
    *collect_data_files("amulet_editor", excludes=["**/*.ui", "**/*.c", "**/*.pyx"]),
    *collect_data_files(
        "amulet_editor.plugins",
        include_py_files=True,
        excludes=["**/*.ui", "**/*.c", "**/*.pyx", "**/*.pyc"],
    ),
    *copy_metadata("amulet_editor", recursive=True),
]

hiddenimports = [
    *collect_submodules("amulet_editor", lambda name: name != "amulet_editor.plugins"),
    *collect_submodules("PySide6"),
    *collect_submodules("OpenGL"),  # On my linux install not everything was included.
]
