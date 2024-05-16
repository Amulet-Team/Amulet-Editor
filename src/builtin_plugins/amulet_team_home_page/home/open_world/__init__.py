from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QApplication, QWidget
from PySide6.QtCore import Qt
from ._open_world import Ui_OpenWorldPage
from amulet_editor.application._cli import spawn_process
from amulet_editor.data.level import get_level
import tablericons


class OpenWorldPage(Ui_OpenWorldPage):
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget):
        super().__init__(parent, f)
        self.btn_back.setIcon(QIcon(tablericons.arrow_left))
        self.load_file_button.clicked.connect(self.open_file)
        self.load_directory_button.clicked.connect(self.open_dir)

    def open_file(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Minecraft files (*.*)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            file, *_ = dialog.selectedFiles()
            spawn_process(file)
            if get_level() is None:
                QApplication.quit()

    def open_dir(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        if dialog.exec():
            file, *_ = dialog.selectedFiles()
            spawn_process(file)
            if get_level() is None:
                QApplication.quit()
