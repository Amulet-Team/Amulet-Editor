import glob
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
)

hiddenimports = collect_submodules("PySide6")
binaries = [(path, ".") for path in glob.glob("Qt/lib/*.so*")]
datas = collect_data_files("PySide6", includes=["*.pyi", "py.typed"])
