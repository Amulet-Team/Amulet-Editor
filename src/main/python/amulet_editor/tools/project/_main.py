import os
from functools import partial
from typing import Optional

import amulet
from amulet_editor.data import build, project
from amulet_editor.application.components import QLinkCard
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.project._ui_panel import Ui_ExplorerPanel
from PySide6.QtCore import QDir, Qt
from PySide6.QtWidgets import QFileSystemModel, QWidget


class ProjectPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)


class ProjectPanel(QWidget, Ui_ExplorerPanel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setupUi(self)

        self.crd_directory = QLinkCard(
            "", build.get_resource(f"icons/folder.svg"), self
        )
        self.frm_directory.layout().addWidget(self.crd_directory)

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(
            QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.Hidden
        )

        self.trv_directory.setContextMenuPolicy(Qt.CustomContextMenu)
        self.trv_directory.setModel(self.model)
        self.trv_directory.hideColumn(1)
        self.trv_directory.hideColumn(2)
        self.trv_directory.hideColumn(3)

        project.changed.connect(self.set_folder)

    def set_folder(self, folder: str) -> None:
        self.level_data = LevelData(amulet.load_format(folder))

        self.trv_directory.setRootIndex(self.model.index(folder))
        self.crd_directory.lbl_description.setText(
            self.level_data.name.get_plain_text()
        )

        try:
            self.crd_directory.clicked.disconnect()
        except RuntimeError:
            pass
        self.crd_directory.clicked.connect(partial(os.startfile, folder))


class Project(AmuletTool):
    def __init__(self) -> None:
        self._page = AmuletView(ProjectPage())
        self._primary_panel = AmuletView(ProjectPanel())
        self._secondary_panel = AmuletView(None)

    @property
    def page(self) -> AmuletView:
        return self._page

    @property
    def primary_panel(self) -> AmuletView:
        return self._primary_panel

    @property
    def secondary_panel(self) -> AmuletView:
        return self._secondary_panel

    @property
    def name(self) -> str:
        return "Project"

    @property
    def icon_name(self) -> str:
        return "folders.svg"
