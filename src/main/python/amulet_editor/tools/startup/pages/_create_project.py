import os
from functools import partial
from shutil import copy, copytree
from typing import Callable, Optional

from amulet_editor.application import appearance
from amulet_editor.data import packages
from amulet_editor.data.project import _files
from amulet_editor.models.generic import Observer
from amulet_editor.tools.programs import Programs
from amulet_editor.tools.project import Project
from amulet_editor.tools.startup._models import Menu, Navigate, ProjectData
from PySide6.QtCore import QCoreApplication, QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProjectGenerator(QObject):

    progress_value = Signal(int)
    progress_max = Signal(int)
    status = Signal(str)

    @Slot(str)
    def generate_project(self, project_data: ProjectData) -> None:
        self.copied_files = 0

        def copy_verbose(source: str, destination: str):
            copy(source, destination)

            file = source.removeprefix(project_data.level_directory)
            self.copied_files += 1
            self.progress_value.emit(self.copied_files)
            self.status.emit(
                '<span style="color: {};">Copying</span> {}'.format(
                    appearance.theme().secondary_variant.get_hex(), source
                )
            )

        self.progress_max.emit(self.get_file_count(project_data.level_directory))

        source = project_data.level_directory
        destination = os.path.join(project_data.directory, project_data.name, "world")
        copytree(source, destination, copy_function=copy_verbose)

    def get_file_count(self, root: str) -> int:
        count = 0
        for path in os.scandir(root):
            if path.is_file():
                count += 1
            else:
                count += self.get_file_count(path)

        return count


class CreateProjectMenu(QObject):

    generate_project = Signal(ProjectData)

    def __init__(self, set_panel: Callable[[Optional[QWidget]], None]) -> None:
        super().__init__()

        self.project_data: Optional[ProjectData] = None
        self.set_panel = set_panel

        self._enable_cancel = Observer(bool)
        self._enable_back = Observer(bool)
        self._enable_next = Observer(bool)

        self._widget = CreateProjectWidget()
        self._widget.btn_create_project.clicked.connect(partial(self.create_project))

        self._generator_thread = QThread()
        self._progress_max = 0

        self.generator = ProjectGenerator()
        self.generate_project.connect(self.generator.generate_project)
        self.generator.progress_value.connect(self.set_progress)
        self.generator.progress_max.connect(self.set_progress_max)
        self.generator.status.connect(self.display_status)
        self.generator.moveToThread(self._generator_thread)

    @property
    def title(self) -> str:
        return "Create Project"

    @property
    def enable_cancel(self) -> Observer:
        return self._enable_cancel

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
        elif destination == Navigate.NEXT:
            tools = packages.list_tools()
            for tool in reversed(tools):
                packages.disable_tool(tool)

            packages.enable_tool(Project())
            packages.enable_tool(Programs())
            _files.open_project(
                os.path.join(self.project_data.directory, self.project_data.name)
            )

    def widget(self) -> QWidget:
        return self._widget

    def next_menu(self) -> Optional[Menu]:
        return None

    def create_project(self) -> None:
        self._widget.btn_create_project.setEnabled(False)
        self._enable_cancel.emit(False)
        self._enable_back.emit(False)

        project_folder = os.path.join(
            self.project_data.directory, self.project_data.name
        )
        try:
            os.makedirs(project_folder)
        except OSError:
            self.project_error("Error: Project already exists")
        else:
            self._generator_thread.start()
            self.generate_project.emit(self.project_data)

    def project_error(self, message: str) -> None:
        txe_project_output = self._widget.txe_project_output
        txe_project_output.appendHtml(
            '<span style="color: {};">{}</span>'.format(
                appearance.theme().error.get_hex(), message
            )
        )

        self._enable_cancel.emit(True)
        self._enable_back.emit(True)

    def set_progress(self, progress: int) -> None:
        self._widget.pbr_project_progress.setValue(progress)
        if progress == self._progress_max and self._generator_thread.isRunning():
            self._generator_thread.exit()
            self._enable_next.emit(True)

    def set_progress_max(self, progress_max: int) -> None:
        self._widget.pbr_project_progress.setRange(0, progress_max)
        self._progress_max = progress_max

    def display_status(self, status: str) -> None:
        self._widget.txe_project_output.appendHtml(status)
        self._widget.txe_project_output.verticalScrollBar().setValue(
            self._widget.txe_project_output.verticalScrollBar().maximum()
        )


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

        # 'Create Project' frame
        lyt_create_project = QHBoxLayout(self)

        self.frm_create_project = QFrame(self)
        self.frm_create_project.setFrameShape(QFrame.NoFrame)
        self.frm_create_project.setFrameShadow(QFrame.Raised)
        self.frm_create_project.setLayout(lyt_create_project)

        self.pbr_project_progress = QProgressBar(self.frm_create_project)
        self.pbr_project_progress.setFixedHeight(30)

        self.btn_create_project = QPushButton(self.frm_create_project)
        self.btn_create_project.setFixedHeight(30)
        self.btn_create_project.setFixedWidth(125)
        self.btn_create_project.setProperty("backgroundColor", "secondary")

        lyt_create_project.addWidget(self.pbr_project_progress)
        lyt_create_project.addWidget(self.btn_create_project)
        lyt_create_project.setContentsMargins(0, 0, 0, 0)
        lyt_create_project.setSpacing(5)

        self.txe_project_output = QPlainTextEdit(self)
        self.txe_project_output.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.txe_project_output.setProperty("border", "surface")
        self.txe_project_output.setProperty("borderRadiusVisible", True)
        self.txe_project_output.setReadOnly(True)
        self.txe_project_output.setWordWrapMode(QTextOption.WordWrap)

        # Create 'Page Content' layout
        layout = QVBoxLayout(self)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_project_overview)
        layout.addWidget(self.frm_project_overview)
        layout.addWidget(self.frm_create_project)
        layout.addWidget(self.txe_project_output)
        layout.setSpacing(5)

        self.setProperty("backgroundColor", "background")
        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_project_overview.setText(QCoreApplication.translate("CreateProjectWidget", "Project Overview", None))
        self.btn_create_project.setText(QCoreApplication.translate("CreateProjectWidget", "Create Project", None))
        # fmt: on
