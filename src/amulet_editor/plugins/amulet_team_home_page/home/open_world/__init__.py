from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QApplication
from amulet_editor.data.build import get_resource
from ._open_world import Ui_OpenWorldPage
from amulet_editor.application._cli import spawn_process
from amulet_editor.data.project import get_level


class OpenWorldPage(Ui_OpenWorldPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btn_back.setIcon(QIcon(get_resource("icons/tabler/arrow-left.svg")))
        self.load_file_button.clicked.connect(self.open_file)
        self.load_directory_button.clicked.connect(self.open_dir)

    def open_file(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Minecraft files (*.*)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            file, *_ = dialog.selectedFiles()
            spawn_process(file)
            if get_level() is None:
                QApplication.quit()

    def open_dir(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        if dialog.exec():
            file, *_ = dialog.selectedFiles()
            spawn_process(file)
            if get_level() is None:
                QApplication.quit()
