from typing import Callable, Optional

from amulet_editor.models.generic import Observer
from amulet_editor.tools.startup._models import Menu, Navigate, ProjectData
from PySide6.QtCore import QCoreApplication, QObject
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CreateProjectMenu(QObject):
    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]) -> None:
        super().__init__()

        self.project_data: Optional[ProjectData] = None
        self.set_panel = set_panel

        self._enable_back = Observer(bool)
        self._enable_next = Observer(bool)

        self._widget = CreateProjectWidget()

    @property
    def title(self) -> str:
        return "Create Project"

    @property
    def enable_back(self) -> Observer:
        return self._enable_back

    @property
    def enable_next(self) -> Observer:
        return self._enable_next

    def navigated(self, destination) -> None:
        if destination == Navigate.HERE:
            self._widget.lbl_project_name.setText(self.project_data.name)
            self._widget.lbl_project_directory.setText(self.project_data.directory)

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        return None


class CreateProjectWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setupUi()

    def setupUi(self):
        # Create 'Project Overview' frame
        self.lbl_project_overview = QLabel(self)
        self.lbl_project_overview.setProperty("color", "on_primary")

        lyt_project_overview = QVBoxLayout(self)

        self.frm_project_overview = QFrame(self)
        self.frm_project_overview.setFrameShape(QFrame.NoFrame)
        self.frm_project_overview.setFrameShadow(QFrame.Raised)
        self.frm_project_overview.setLayout(lyt_project_overview)
        self.frm_project_overview.setProperty("backgroundColor", "primary")
        self.frm_project_overview.setProperty("border", "surface")
        self.frm_project_overview.setProperty("borderRadiusVisible", True)

        self.lbl_project_name = QLabel(self.frm_project_overview)
        self.lbl_project_name.setProperty("color", "on_primary")
        self.lbl_project_name.setProperty("subfamily", "semi_bold")

        self.lbl_project_directory = QLabel(self.frm_project_overview)
        self.lbl_project_directory.setProperty("color", "on_surface")

        lyt_project_overview.addWidget(self.lbl_project_name)
        lyt_project_overview.addWidget(self.lbl_project_directory)
        lyt_project_overview.setSpacing(5)

        self.btn_create_project = QPushButton(self)
        self.btn_create_project.setFixedHeight(30)
        self.btn_create_project.setProperty("backgroundColor", "secondary")

        # Create 'Project Status' frame
        self.lbl_project_status = QLabel(self)
        self.lbl_project_status.setProperty("color", "on_primary")

        self.pbr_project_status = QProgressBar(self)
        self.pbr_project_status.setValue(75)
        self.pbr_project_status.setRange(0, 100)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_overview)
        layout.addWidget(self.frm_project_overview)
        layout.addWidget(self.btn_create_project)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_status)
        layout.addWidget(self.pbr_project_status)
        layout.addStretch()
        layout.setSpacing(5)

        self.setProperty("backgroundColor", "background")
        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_project_overview.setText(QCoreApplication.translate("CreateProjectWidget", "Project Overview", None))
        self.btn_create_project.setText(QCoreApplication.translate("CreateProjectWidget", "Create Project", None))
        self.lbl_project_status.setText(QCoreApplication.translate("CreateProjectWidget", "Project Status", None))
        # fmt: on
