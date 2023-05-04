import os
from functools import partial
from typing import Callable, Optional

from amulet_editor.data import packages, paths, project
from amulet_editor.models.generic import Observer
from amulet_editor.models.widgets import AIconButton
from amulet_editor.tools.programs import Programs
from amulet_editor.tools.project import Project
from amulet_editor.tools.startup._models import Menu, Navigate, ProjectData
from amulet_editor.tools.startup.pages._import_level import ImportLevelMenu
from PySide6.QtCore import QCoreApplication, QObject, QSize
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class NewProjectMenu(QObject):
    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]):
        super().__init__()

        self.level_directory: Optional[str] = None
        self.project_data = ProjectData(name="", directory=paths.project_directory())
        self.set_panel = set_panel

        self._enable_next = Observer(bool)

        self._widget = NewProjectWidget()
        self._widget.btn_project_directory.clicked.connect(partial(self.select_folder))
        self._widget.lne_project_directory.setText(self.project_data.directory)
        self._widget.lne_project_name.textChanged.connect(self.check_enable_next)

    @property
    def title(self) -> str:
        return "New Project"

    @property
    def enable_next(self) -> Observer:
        return self._enable_next

    def navigated(self, destination):
        if destination == Navigate.HERE:
            project_name = self._widget.lne_project_name.text().strip()
            self._enable_next.emit(len(project_name) > 0)

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        menu = ImportLevelMenu(self.set_panel)
        menu.set_project_data(self.project_data)
        return menu

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Folder",
            os.path.realpath(self.project_data.directory),
            QFileDialog.Option.ShowDirsOnly,
        )

        if os.path.isdir(folder):
            folder = str(os.path.sep).join(folder.split("/"))
            self.project_data.directory = folder
            self._widget.lne_project_directory.setText(folder)

    def check_enable_next(self, project_name: str):
        project_name = project_name.strip()
        self.project_data.name = project_name
        self._enable_next.emit(len(project_name) > 0)


class NewProjectWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setupUi()

    def setupUi(self):
        # 'Project Name' field
        self.lbl_project_name = QLabel(self)
        self.lbl_project_name.setProperty("color", "on_primary")

        self.lne_project_name = QLineEdit(self)
        self.lne_project_name.setFixedHeight(25)

        # 'Project Directory' field
        self.lbl_project_directory = QLabel(self)
        self.lbl_project_directory.setProperty("color", "on_primary")

        self.frm_project_directory = QFrame(self)

        lyt_project_directory = QHBoxLayout(self.frm_project_directory)

        self.lne_project_directory = QLineEdit(self.frm_project_directory)
        self.lne_project_directory.setFixedHeight(25)
        self.lne_project_directory.setProperty("color", "on_surface")
        self.lne_project_directory.setReadOnly(True)

        self.btn_project_directory = AIconButton(
            "folder.svg", self.frm_project_directory
        )
        self.btn_project_directory.setFixedSize(QSize(27, 27))
        self.btn_project_directory.setIconSize(QSize(15, 15))
        self.btn_project_directory.setProperty("backgroundColor", "primary")

        lyt_project_directory.addWidget(self.lne_project_directory)
        lyt_project_directory.addWidget(self.btn_project_directory)
        lyt_project_directory.setContentsMargins(0, 0, 0, 0)
        lyt_project_directory.setSpacing(5)

        self.frm_project_directory.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_project_directory.setFrameShadow(QFrame.Shadow.Raised)
        self.frm_project_directory.setLayout(lyt_project_directory)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_name)
        layout.addWidget(self.lne_project_name)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_directory)
        layout.addWidget(self.frm_project_directory)
        layout.addStretch()
        layout.setSpacing(5)

        self.setProperty("backgroundColor", "background")
        self.setLayout(layout)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_project_name.setText(QCoreApplication.translate("NewProjectTypePage", "Project Name", None))
        self.lbl_project_directory.setText(QCoreApplication.translate("NewProjectTypePage", "Project Directory", None))
        # fmt: on
