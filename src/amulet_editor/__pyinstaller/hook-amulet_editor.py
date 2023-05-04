try:
    from PyInstaller.utils.hooks import collect_data_files
except ImportError as e:
    raise ImportError(
        "This is part of the build pipeline. It cannot be imported at runtime."
    ) from e

datas = collect_data_files("amulet_editor")
