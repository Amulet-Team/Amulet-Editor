import glob
import os
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
)

import PySide6

hiddenimports = collect_submodules("PySide6")
binaries = [(path, ".") for path in glob.glob(os.path.join(glob.escape(PySide6.__path__[0]), "Qt", "lib", "*.so*"))]
datas = collect_data_files("PySide6", includes=["*.pyi", "py.typed"])
