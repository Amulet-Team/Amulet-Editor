import os
from functools import partial
from typing import Optional

import amulet
from amulet_editor.data import build, project
from PySide6.QtCore import QDir, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class ProgramsPanel(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.setupUi()

    def print_directory(self):
        file = self.model.filePath(self.trv_directory.selectedIndexes()[0])

        self.file_selected.emit(file)

    def set_folder(self, folder: str):
        self.trv_directory.setRootIndex(self.model.index(folder))
        self.crd_directory.lbl_description.setText(
            ""
            # self.level_data.name.get_plain_text()
        )

        try:
            self.crd_directory.clicked.disconnect()
        except RuntimeError:
            pass
        self.crd_directory.clicked.connect(partial(os.startfile, folder))

    def setupUi(self):
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frm_directory = QFrame(self)
        self.frm_directory.setObjectName("frm_directory")
        self.frm_directory.setMinimumSize(QSize(0, 24))
        self.frm_directory.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_directory.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frm_directory)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)

        self.verticalLayout.addWidget(self.frm_directory)

        self.trv_directory = QTreeView(self)
        self.trv_directory.setObjectName("trv_directory")
        self.trv_directory.setFrameShape(QFrame.Shape.NoFrame)
        self.trv_directory.setIndentation(8)
        self.trv_directory.setUniformRowHeights(True)
        self.trv_directory.setHeaderHidden(True)
        self.trv_directory.header().setVisible(False)

        self.verticalLayout.addWidget(self.trv_directory)
