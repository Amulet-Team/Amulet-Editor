from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QWidget
from PySide6.QtCore import Qt

from amulet.level import get_level
from amulet.level.loader import LevelLoaderPathToken

from amulet.app.exception import CatchExceptionDialog

from plugin.tablericons import tablericons

from ._open_world_page_gui import OpenWorldPageGui


class OpenWorldPage(OpenWorldPageGui):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self.btn_back.setIcon(QIcon(tablericons.outline.arrow_left))
        self.load_file_button.clicked.connect(self._open_file)
        self.load_directory_button.clicked.connect(self._open_dir)

    def _open_file(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Minecraft files (*.*)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            path, *_ = dialog.selectedFiles()
            self._open_level(path)

    def _open_dir(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        if dialog.exec():
            path, *_ = dialog.selectedFiles()
            self._open_level(path)

    @staticmethod
    def _open_level(path: str) -> None:
        with CatchExceptionDialog("Failed opening level"):
            from ..._main_window import get_amulet_editor_api

            level = get_level(LevelLoaderPathToken(path))
            with level.lock():
                level.open()
            get_amulet_editor_api().add_level_tab(level, show=True)
