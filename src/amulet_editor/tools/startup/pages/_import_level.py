import os
from functools import partial
from typing import Callable, Optional

import amulet
from amulet_editor.data import minecraft, paths
from amulet_editor.models.generic import Observer
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.widgets import AIconButton
from amulet_editor.tools.startup._models import Menu, ProjectData
from amulet_editor.tools.startup._widgets import QLevelSelectionCard
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


class ImportLevelMenu(QObject):
    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]):
        super().__init__()

        self.project_directory = paths.project_directory()

        self.level_directory: Optional[str] = None
        self.project_data: Optional[ProjectData] = None
        self.set_panel = set_panel

        self._enable_next = Observer(bool)

        self._widget = ImportLevelWidget()
        self._widget.btn_import_level.clicked.connect(partial(self.import_level))
        self._widget.crd_select_level.clicked.connect(partial(self.select_level))

        self._world_selection_panel = WorldSelectionPanel()
        self._world_selection_panel.level_data.connect(self.set_level)

        QApplication.instance().focusChanged.connect(self.check_focus)

    @property
    def title(self) -> str:
        return "New Project"

    @property
    def enable_next(self) -> Observer:
        return self._enable_next

    def navigated(self, destination):
        pass

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        return None

    def import_level(self):
        path = QFileDialog.getExistingDirectory(
            None,
            "Select Minecraft World",
            os.path.realpath(minecraft.save_directories()[0]),
            QFileDialog.Option.ShowDirsOnly,
        )
        self._widget.btn_import_level.setChecked(False)

        if os.path.exists(os.path.join(path, "level.dat")):
            path = str(os.path.sep).join(path.split("/"))

            level_data = LevelData(amulet.load_format(path))
            self.set_level(level_data)

    def select_level(self):
        if self._widget.crd_select_level.isChecked():
            self.set_panel(self._world_selection_panel)
        else:
            self.set_panel(None)

    def set_level(self, level_data: LevelData):
        self.project_data.level_directory = level_data.path

        self._widget.lne_import_level.setText(level_data.path)
        self._widget.crd_select_level.setLevel(level_data)

        self.enable_next.emit(True)

    def set_project_data(self, project_data: ProjectData):
        self.project_data = project_data

    def check_focus(self, old: Optional[QWidget], new: Optional[QWidget]):
        alternate_focus = [self._widget.lne_import_level]

        if new in alternate_focus:
            self.uncheck_level_card()

    def uncheck_level_card(self):
        self._widget.crd_select_level.setChecked(False)
        self._widget.crd_select_level.clicked.emit()


class ImportLevelWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setupUi()

    def setupUi(self):
        # Create 'Select Level' frame
        self.lbl_select_level = QLabel(self)
        self.lbl_select_level.setProperty("color", "on_primary")

        lyt_import_level = QHBoxLayout(self)

        self.frm_import_level = QFrame(self)
        self.frm_import_level.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_import_level.setFrameShadow(QFrame.Shadow.Raised)
        self.frm_import_level.setLayout(lyt_import_level)

        self.lne_import_level = QLineEdit(self.frm_import_level)
        self.lne_import_level.setFixedHeight(25)
        self.lne_import_level.setProperty("color", "on_surface")
        self.lne_import_level.setReadOnly(True)

        self.btn_import_level = AIconButton("folder.svg", self.frm_import_level)
        self.btn_import_level.setCheckable(True)
        self.btn_import_level.setFixedSize(QSize(27, 27))
        self.btn_import_level.setIconSize(QSize(15, 15))
        self.btn_import_level.setProperty("backgroundColor", "primary")

        lyt_import_level.addWidget(self.lne_import_level)
        lyt_import_level.addWidget(self.btn_import_level)
        lyt_import_level.setContentsMargins(0, 0, 0, 0)
        lyt_import_level.setSpacing(5)

        self.crd_select_level = QLevelSelectionCard(self)
        self.crd_select_level.setCheckable(True)
        self.crd_select_level.setFixedHeight(105)
        self.crd_select_level.setProperty("backgroundColor", "primary")
        self.crd_select_level.setProperty("border", "surface")
        self.crd_select_level.setProperty("borderRadiusVisible", True)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_select_level)
        layout.addWidget(self.frm_import_level)
        layout.addWidget(self.crd_select_level)
        layout.addStretch()
        layout.setSpacing(5)

        self.setProperty("backgroundColor", "background")
        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_select_level.setText(QCoreApplication.translate("NewProjectTypePage", "Select World", None))
        # fmt: on
