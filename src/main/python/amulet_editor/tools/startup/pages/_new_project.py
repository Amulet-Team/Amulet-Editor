import os
from functools import partial

from amulet_editor.data import paths
from amulet_editor.tools.startup._components import QIconButton
from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class NewProjectPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.project_directory = paths.project_directory()

        self.setupUi()

        self.btn_back.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_project_directory.clicked.connect(partial(self.select_folder))

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Folder",
            os.path.realpath(self.project_directory),
            QFileDialog.ShowDirsOnly,
        )

        if os.path.isdir(folder):
            folder = str(os.path.sep).join(folder.split("/"))
            self.project_directory = folder
            self.lne_project_directory.setText(folder)

    def setupUi(self):
        # Create 'Inner Container' frame
        self.frm_inner_container = QFrame(self)
        self.frm_inner_container.setFrameShape(QFrame.NoFrame)
        self.frm_inner_container.setFrameShadow(QFrame.Raised)
        self.frm_inner_container.setMaximumWidth(750)
        self.frm_inner_container.setProperty("borderLeft", "surface")
        self.frm_inner_container.setProperty("borderRight", "surface")

        # Create 'Header' frame
        self.frm_header = QFrame(self.frm_inner_container)

        self.lbl_header = QLabel(self.frm_header)
        self.lbl_header.setProperty("heading", "h3")
        self.lbl_header.setProperty("subfamily", "semi_light")

        lyt_header = QHBoxLayout(self.frm_header)
        lyt_header.addWidget(self.lbl_header)
        lyt_header.setAlignment(Qt.AlignLeft)
        lyt_header.setContentsMargins(0, 0, 0, 10)
        lyt_header.setSpacing(5)

        self.frm_header.setFrameShape(QFrame.NoFrame)
        self.frm_header.setFrameShadow(QFrame.Raised)
        self.frm_header.setLayout(lyt_header)
        self.frm_header.setProperty("borderBottom", "surface")
        self.frm_header.setProperty("borderTop", "background")

        # 'Scroll Container' widget
        self.scr_container = QScrollArea()
        self.wgt_container = QWidget(self.scr_container)
        self.lyt_container = QVBoxLayout()

        self.lyt_container.setContentsMargins(0, 0, 0, 0)
        self.wgt_container.setLayout(self.lyt_container)
        self.wgt_container.setProperty("backgroundColor", "background")
        self.scr_container.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scr_container.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scr_container.setWidgetResizable(True)
        self.scr_container.setFrameShape(QFrame.NoFrame)
        self.scr_container.setFrameShadow(QFrame.Raised)
        self.scr_container.setWidget(self.wgt_container)

        # 'Project Name' field
        self.lbl_project_name = QLabel(self.wgt_container)
        self.lbl_project_name.setProperty("color", "on_primary")

        self.lne_project_name = QLineEdit(self.wgt_container)
        self.lne_project_name.setFixedHeight(25)

        # 'Project Directory' field
        self.lbl_project_directory = QLabel(self.wgt_container)
        self.lbl_project_directory.setProperty("color", "on_primary")

        self.frm_project_directory = QFrame(self.wgt_container)

        lyt_project_directory = QHBoxLayout(self.frm_project_directory)

        self.lne_project_directory = QLineEdit(self.frm_project_directory)
        self.lne_project_directory.setFixedHeight(25)
        self.lne_project_directory.setProperty("color", "on_surface")
        self.lne_project_directory.setReadOnly(True)
        self.lne_project_directory.setText(self.project_directory)

        self.btn_project_directory = QIconButton(self.frm_project_directory)
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

        # Add widgets to 'Scroll Container'
        self.lyt_container.addSpacing(10)
        self.lyt_container.addWidget(self.lbl_project_name)
        self.lyt_container.addWidget(self.lne_project_name)
        self.lyt_container.addSpacing(10)
        self.lyt_container.addWidget(self.lbl_project_directory)
        self.lyt_container.addWidget(self.frm_project_directory)
        self.lyt_container.addStretch()

        # Create 'Page Options' frame
        self.frm_page_options = QFrame(self)

        # Configure 'Page Options' widgets
        self.btn_cancel = QPushButton(self.frm_page_options)
        self.btn_cancel.setFixedHeight(30)

        self.btn_back = QPushButton(self.frm_page_options)
        self.btn_back.setFixedHeight(30)

        self.btn_next = QPushButton(self.frm_page_options)
        self.btn_next.setFixedHeight(30)
        self.btn_next.setProperty("backgroundColor", "secondary")

        # Create 'Page Options' layout
        lyt_page_options = QHBoxLayout(self.frm_inner_container)
        lyt_page_options.addWidget(self.btn_cancel)
        lyt_page_options.addStretch()
        lyt_page_options.addWidget(self.btn_back)
        lyt_page_options.addWidget(self.btn_next)
        lyt_page_options.setContentsMargins(0, 10, 0, 5)
        lyt_page_options.setSpacing(5)

        # Configure 'Page Options' frame
        self.frm_page_options.setFrameShape(QFrame.NoFrame)
        self.frm_page_options.setFrameShadow(QFrame.Raised)
        self.frm_page_options.setLayout(lyt_page_options)
        self.frm_page_options.setProperty("borderTop", "surface")

        # Create 'Inner Frame' layout
        lyt_inner_frame = QVBoxLayout(self.frm_inner_container)
        lyt_inner_frame.addWidget(self.frm_header)
        lyt_inner_frame.addWidget(self.scr_container)
        lyt_inner_frame.addWidget(self.frm_page_options)
        lyt_inner_frame.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lyt_inner_frame.setSpacing(5)

        # Configure 'Page' layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.frm_inner_container)
        layout.setAlignment(Qt.AlignHCenter)

        self.setLayout(layout)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_header.setText(QCoreApplication.translate("NewProjectTypePage", "New Project", None))
        self.lbl_project_name.setText(QCoreApplication.translate("NewProjectTypePage", "Project Name", None))
        self.lbl_project_directory.setText(QCoreApplication.translate("NewProjectTypePage", "Project Directory", None))
        self.btn_cancel.setText(QCoreApplication.translate("NewProjectTypePage", "Cancel", None))
        self.btn_back.setText(QCoreApplication.translate("NewProjectTypePage", "Back", None))
        self.btn_next.setText(QCoreApplication.translate("NewProjectTypePage", "Next", None))
        # fmt: on
