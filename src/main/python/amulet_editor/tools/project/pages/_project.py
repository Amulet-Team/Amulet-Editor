import os
from os import R_OK
from typing import Optional

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class ProjectPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.setupUi()

    def show_file(self, file_path: str) -> None:
        if os.path.isfile(file_path) and os.access(file_path, R_OK):
            try:
                with open(file_path, "r") as text:
                    self.txe_file.setText(text.read())
            except UnicodeDecodeError:
                self.txe_file.setText(f"Unable to Decode File:\n{file_path}")

    def setupUi(self) -> None:
        self.txe_file = QTextEdit()
        self.txe_file.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txe_file)

        self.setLayout(layout)
