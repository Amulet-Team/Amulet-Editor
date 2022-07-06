import os
from functools import partial
from typing import Callable, Optional, Union

import amulet
from amulet_editor.data import paths
from amulet_editor.models.generic import Observer
from amulet_editor.models.minecraft import LevelData
from amulet_editor.tools.startup._models import Menu, Navigate, ProjectData
from amulet_editor.tools.startup._widgets import QIconButton, QLevelSelectionCard
from amulet_editor.tools.startup.pages._import_level import ImportLevelMenu
from amulet_editor.tools.startup.panels._world_selection import WorldSelectionPanel
from PySide6.QtCore import QCoreApplication, QObject, QSize
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class NewProjectMenu(QObject):
    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]) -> None:
        super().__init__()

        self.project_data = ProjectData(name="", directory=paths.project_directory())
        self.set_panel = set_panel

        self._enable_next = Observer(bool)

        self._widget = NewProjectWidget()
        self._widget.btn_level_directory.clicked.connect(partial(self.import_level))
        self._widget.btn_project_directory.clicked.connect(partial(self.select_folder))
        self._widget.crd_select_level.clicked.connect(partial(self.select_level))
        self._widget.lne_project_directory.setText(self.project_data.directory)
        self._widget.lne_project_name.textChanged.connect(self.set_project_name)

        self._world_selection_panel = WorldSelectionPanel()
        self._world_selection_panel.level_data.connect(self.set_level)

        QApplication.instance().focusChanged.connect(self.check_focus)

    @property
    def title(self) -> str:
        return "New Project"

    @property
    def enable_next(self) -> Observer:
        return self._enable_next

    def navigated(self, destination) -> None:
        if destination == Navigate.HERE:
            self.check_enable_next()

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        menu = ImportLevelMenu(self.set_panel)
        menu.set_project_data(self.project_data)
        return menu

    def set_project_name(self, project_name: str) -> None:
        self.project_data.name = project_name
        self.check_enable_next()

    def select_folder(self) -> None:
        self.uncheck_level_card()

        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Folder",
            os.path.realpath(self.project_data.directory),
            QFileDialog.ShowDirsOnly,
        )

        self._widget.btn_project_directory.setChecked(False)

        if os.path.isdir(folder):
            folder = str(os.path.sep).join(folder.split("/"))
            self.project_data.directory = folder
            self._widget.lne_project_directory.setText(folder)

    def check_enable_next(self) -> None:
        valid_name = len(self.project_data.name) > 0
        valid_level = self.project_data.level_directory is not None and os.path.isfile(
            os.path.join(self.project_data.level_directory, "level.dat")
        )

        self._enable_next.emit(valid_name and valid_level)

    def import_level(self) -> None:
        self.uncheck_level_card()

        path = self._widget.lne_level_directory.text()
        path = os.path.expanduser("~") if path == "" else path
        path = QFileDialog.getExistingDirectory(
            None,
            "Select Minecraft World",
            os.path.realpath(path),
            QFileDialog.ShowDirsOnly,
        )

        self._widget.btn_level_directory.setChecked(False)
        self.set_level(path)

    def select_level(self):
        if self._widget.crd_select_level.isChecked():
            self.set_panel(self._world_selection_panel)
        else:
            self.set_panel(None)

    def set_level(self, level: Union[str, LevelData]) -> None:
        if isinstance(level, str):
            path = str(os.path.sep).join(level.split("/"))

        if isinstance(level, LevelData):
            self.project_data.level_directory = level.path

            self._widget.lne_level_directory.setText(level.path)
            self._widget.crd_select_level.setLevel(level)
        elif os.path.isfile(os.path.join(path, "level.dat")):
            level_data = LevelData(amulet.load_format(path))

            self.project_data.level_directory = level_data.path

            self._widget.lne_level_directory.setText(level_data.path)
            self._widget.crd_select_level.setLevel(level_data)
        else:
            self.project_data.level_directory = None

            self._widget.lne_level_directory.setText(path)
            self._widget.crd_select_level.setLevel(None)

        self.check_enable_next()

    def check_focus(self, old: Optional[QWidget], new: Optional[QWidget]):
        alternate_focus = [
            self._widget.lne_level_directory,
            self._widget.lne_project_directory,
            self._widget.lne_project_name,
        ]

        if new in alternate_focus:
            self.uncheck_level_card()

    def uncheck_level_card(self) -> None:
        self._widget.crd_select_level.setChecked(False)
        self._widget.crd_select_level.clicked.emit()


class NewProjectWidget(QWidget):
    def __init__(self) -> None:
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

        self.btn_project_directory = QIconButton(self.frm_project_directory)
        self.btn_project_directory.setCheckable(True)
        self.btn_project_directory.setFixedSize(QSize(27, 27))
        self.btn_project_directory.setIcon("folder.svg")
        self.btn_project_directory.setIconSize(QSize(15, 15))
        self.btn_project_directory.setProperty("backgroundColor", "primary")

        lyt_project_directory.addWidget(self.lne_project_directory)
        lyt_project_directory.addWidget(self.btn_project_directory)
        lyt_project_directory.setContentsMargins(0, 0, 0, 0)
        lyt_project_directory.setSpacing(5)

        self.frm_project_directory.setFrameShape(QFrame.NoFrame)
        self.frm_project_directory.setFrameShadow(QFrame.Raised)
        self.frm_project_directory.setLayout(lyt_project_directory)

        # 'Import Level' field
        self.lbl_import_level = QLabel(self)
        self.lbl_import_level.setProperty("color", "on_primary")

        self.frm_import_level = QFrame(self)

        lyt_import_level = QVBoxLayout(self.frm_import_level)

        self.frm_import_level.setFrameShape(QFrame.NoFrame)
        self.frm_import_level.setFrameShadow(QFrame.Raised)
        self.frm_import_level.setLayout(lyt_import_level)
        self.frm_import_level.setProperty("border", "surface")
        self.frm_import_level.setProperty("borderBottom", "none")
        self.frm_import_level.setProperty("borderRight", "none")
        self.frm_import_level.setProperty("borderTop", "none")

        # 'Select Level' field
        self.lbl_select_level = QLabel(self)
        self.lbl_select_level.setProperty("color", "on_surface")

        self.crd_select_level = QLevelSelectionCard(self)
        self.crd_select_level.setCheckable(True)
        self.crd_select_level.setFixedHeight(105)
        self.crd_select_level.setProperty("backgroundColor", "primary")
        self.crd_select_level.setProperty("border", "surface")
        self.crd_select_level.setProperty("borderRadiusVisible", True)

        # 'Level Directory' field
        self.lbl_level_directory = QLabel(self)
        self.lbl_level_directory.setProperty("color", "on_surface")

        lyt_level_directory = QHBoxLayout(self)

        self.frm_level_directory = QFrame(self)
        self.frm_level_directory.setFrameShape(QFrame.NoFrame)
        self.frm_level_directory.setFrameShadow(QFrame.Raised)
        self.frm_level_directory.setLayout(lyt_level_directory)

        self.lne_level_directory = QLineEdit(self.frm_level_directory)
        self.lne_level_directory.setFixedHeight(25)
        self.lne_level_directory.setProperty("color", "on_surface")
        self.lne_level_directory.setReadOnly(True)

        self.btn_level_directory = QIconButton(self.frm_level_directory)
        self.btn_level_directory.setCheckable(True)
        self.btn_level_directory.setFixedSize(QSize(27, 27))
        self.btn_level_directory.setIcon("folder.svg")
        self.btn_level_directory.setIconSize(QSize(15, 15))
        self.btn_level_directory.setProperty("backgroundColor", "primary")

        lyt_level_directory.addWidget(self.lne_level_directory)
        lyt_level_directory.addWidget(self.btn_level_directory)
        lyt_level_directory.setContentsMargins(0, 0, 0, 0)
        lyt_level_directory.setSpacing(5)

        # Configure 'Import Level' layout
        lyt_import_level.addWidget(self.lbl_select_level)
        lyt_import_level.addWidget(self.crd_select_level)
        lyt_import_level.addSpacing(10)
        lyt_import_level.addWidget(self.lbl_level_directory)
        lyt_import_level.addWidget(self.frm_level_directory)
        lyt_import_level.setContentsMargins(10, 5, 0, 5)
        lyt_import_level.setSpacing(5)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_name)
        layout.addWidget(self.lne_project_name)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_directory)
        layout.addWidget(self.frm_project_directory)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_import_level)
        layout.addWidget(self.frm_import_level)
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
        self.lbl_import_level.setText(QCoreApplication.translate("NewProjectTypePage", "Import World", None))
        self.lbl_select_level.setText(QCoreApplication.translate("NewProjectTypePage", "Select World", None))
        self.lbl_level_directory.setText(QCoreApplication.translate("NewProjectTypePage", "World Directory", None))
        # fmt: on
