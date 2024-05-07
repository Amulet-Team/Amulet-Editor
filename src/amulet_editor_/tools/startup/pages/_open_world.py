import os
from functools import partial
from typing import Callable, Optional, Union

import amulet
from amulet_editor.data import packages, project
from amulet_editor.models.generic import Observer
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.widgets import AIconButton
from amulet_editor.tools.programs import Programs
from amulet_editor.tools.project import Project
from amulet_editor.tools.startup._models import Menu, Navigate
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


class OpenWorldMenu(QObject):
    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]):
        super().__init__()

        self.level_directory: Optional[str] = None
        self.set_panel = set_panel

        self._enable_next = Observer(bool)

        self._widget = OpenWorldWidget()
        self._widget.btn_level_directory.clicked.connect(partial(self.import_level))
        self._widget.crd_select_level.clicked.connect(partial(self.select_level))

        self._world_selection_panel = WorldSelectionPanel()
        self._world_selection_panel.level_data.connect(self.set_level)

        QApplication.instance().focusChanged.connect(self.check_focus)

    @property
    def title(self) -> str:
        return "Open World"

    @property
    def enable_next(self) -> Observer:
        return self._enable_next

    def navigated(self, destination):
        if destination == Navigate.NEXT:
            tools = packages.list_tools()
            for tool in reversed(tools):
                packages.disable_tool(tool)

            packages.enable_tool(Project())
            packages.enable_tool(Programs())
            project.set_root(self.level_directory)

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        return None

    def import_level(self):
        self.uncheck_level_card()

        path = self._widget.lne_level_directory.text()
        path = os.path.expanduser("~") if path == "" else path
        path = QFileDialog.getExistingDirectory(
            None,
            "Select Minecraft World",
            os.path.realpath(path),
            QFileDialog.Option.ShowDirsOnly,
        )
        self._widget.btn_level_directory.setChecked(False)
        self.set_level(path)

    def select_level(self):
        if self._widget.crd_select_level.isChecked():
            self.set_panel(self._world_selection_panel)
        else:
            self.set_panel(None)

    def set_level(self, level: Union[str, LevelData]):
        if isinstance(level, str):
            path = str(os.path.sep).join(level.split("/"))

        if isinstance(level, LevelData):
            self.level_directory = level.path

            self._widget.lne_level_directory.setText(level.path)
            self._widget.crd_select_level.setLevel(level)

            self.enable_next.emit(True)
        elif os.path.isfile(os.path.join(path, "level.dat")):
            level_data = LevelData(amulet.load_format(path))

            self.level_directory = level_data.path

            self._widget.lne_level_directory.setText(level_data.path)
            self._widget.crd_select_level.setLevel(level_data)

            self.enable_next.emit(True)
        else:
            self._widget.lne_level_directory.setText(path)
            self._widget.crd_select_level.setLevel(None)

            self.enable_next.emit(False)

    def check_focus(self, old: Optional[QWidget], new: Optional[QWidget]):
        alternate_focus = [self._widget.lne_level_directory]

        if new in alternate_focus:
            self.uncheck_level_card()

    def uncheck_level_card(self):
        self._widget.crd_select_level.setChecked(False)
        self._widget.crd_select_level.clicked.emit()


class OpenWorldWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setupUi()

    def setupUi(self):
        # Configure 'Select Level'
        self.lbl_select_level = QLabel(self)
        self.lbl_select_level.setProperty("color", "on_primary")

        self.crd_select_level = QLevelSelectionCard(self)
        self.crd_select_level.setCheckable(True)
        self.crd_select_level.setFixedHeight(105)
        self.crd_select_level.setProperty("backgroundColor", "primary")
        self.crd_select_level.setProperty("border", "surface")
        self.crd_select_level.setProperty("borderRadiusVisible", True)

        # Configure 'Level Directory'
        self.lbl_level_directory = QLabel(self)
        self.lbl_level_directory.setProperty("color", "on_primary")

        lyt_level_directory = QHBoxLayout(self)

        self.frm_level_directory = QFrame(self)
        self.frm_level_directory.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_level_directory.setFrameShadow(QFrame.Shadow.Raised)
        self.frm_level_directory.setLayout(lyt_level_directory)

        self.lne_level_directory = QLineEdit(self.frm_level_directory)
        self.lne_level_directory.setFixedHeight(25)
        self.lne_level_directory.setProperty("color", "on_surface")
        self.lne_level_directory.setReadOnly(True)

        self.btn_level_directory = AIconButton("folder.svg", self.frm_level_directory)
        self.btn_level_directory.setCheckable(True)
        self.btn_level_directory.setFixedSize(QSize(27, 27))
        self.btn_level_directory.setIconSize(QSize(15, 15))
        self.btn_level_directory.setProperty("backgroundColor", "primary")

        lyt_level_directory.addWidget(self.lne_level_directory)
        lyt_level_directory.addWidget(self.btn_level_directory)
        lyt_level_directory.setContentsMargins(0, 0, 0, 0)
        lyt_level_directory.setSpacing(5)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_select_level)
        layout.addWidget(self.crd_select_level)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_level_directory)
        layout.addWidget(self.frm_level_directory)
        layout.addStretch()
        layout.setSpacing(5)

        self.setProperty("backgroundColor", "background")
        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_select_level.setText(QCoreApplication.translate("NewProjectTypePage", "Select World", None))
        self.lbl_level_directory.setText(QCoreApplication.translate("NewProjectTypePage", "World Directory", None))
        # fmt: on
