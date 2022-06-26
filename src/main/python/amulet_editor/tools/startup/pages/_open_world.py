import os
from functools import partial
from typing import Optional

import amulet
from amulet_editor.data import minecraft
from amulet_editor.models.minecraft import LevelData
from amulet_editor.tools.startup._components import QIconButton, QLevelSelectionCard
from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
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


class OpenWorldPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.level_directory = None

        self.setupUi()

        self.btn_back.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_import_level.clicked.connect(partial(self.browse_levels))

        QApplication.instance().focusChanged.connect(self.check_focus)

    def browse_levels(self) -> None:
        self.uncheck_level_card()

        path = QFileDialog.getExistingDirectory(
            None,
            "Select Minecraft World",
            os.path.realpath(minecraft.save_directories()[0]),
            QFileDialog.ShowDirsOnly,
        )
        self.btn_import_level.setChecked(False)

        if os.path.exists(os.path.join(path, "level.dat")):
            path = str(os.path.sep).join(path.split("/"))

            level_data = LevelData(amulet.load_format(path))
            self.select_level(level_data)

    def check_focus(self, old: Optional[QWidget], new: Optional[QWidget]):
        alternate_focus = [self.btn_back, self.btn_next, self.lne_import_level]

        if new in alternate_focus:
            self.uncheck_level_card()

    def uncheck_level_card(self) -> None:
        self.crd_select_level.setChecked(False)
        self.crd_select_level.clicked.emit()

    def select_level(self, level_data: LevelData) -> None:
        self.level_directory = level_data.path

        self.lne_import_level.setText(level_data.path)
        self.crd_select_level.setLevel(level_data)

        self.btn_next.setEnabled(True)

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

        # Central scrollable field
        self.scr_recent = QScrollArea()
        self.wgt_recent = QWidget(self.scr_recent)
        self.lyt_recent = QVBoxLayout()

        self.lyt_recent.addStretch()
        self.lyt_recent.setContentsMargins(0, 0, 5, 0)
        self.wgt_recent.setLayout(self.lyt_recent)
        self.wgt_recent.setProperty("style", "background")
        self.scr_recent.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scr_recent.setProperty("style", "background")
        self.scr_recent.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scr_recent.setWidgetResizable(True)
        self.scr_recent.setWidget(self.wgt_recent)

        # Create 'Select Level' frame
        self.lbl_select_level = QLabel(self.frm_inner_container)
        self.lbl_select_level.setProperty("color", "on_primary")

        lyt_import_level = QHBoxLayout(self.frm_inner_container)

        self.frm_import_level = QFrame(self.frm_inner_container)
        self.frm_import_level.setFrameShape(QFrame.NoFrame)
        self.frm_import_level.setFrameShadow(QFrame.Raised)
        self.frm_import_level.setLayout(lyt_import_level)

        self.lne_import_level = QLineEdit(self.frm_import_level)
        self.lne_import_level.setFixedHeight(25)
        self.lne_import_level.setProperty("color", "on_surface")
        self.lne_import_level.setReadOnly(True)

        self.btn_import_level = QIconButton(self.frm_import_level)
        self.btn_import_level.setCheckable(True)
        self.btn_import_level.setFixedSize(QSize(27, 27))
        self.btn_import_level.setIcon("folder.svg")
        self.btn_import_level.setIconSize(QSize(15, 15))
        self.btn_import_level.setProperty("backgroundColor", "primary")

        lyt_import_level.addWidget(self.lne_import_level)
        lyt_import_level.addWidget(self.btn_import_level)
        lyt_import_level.setContentsMargins(0, 0, 0, 0)
        lyt_import_level.setSpacing(5)

        self.crd_select_level = QLevelSelectionCard(self.frm_inner_container)
        self.crd_select_level.setCheckable(True)
        self.crd_select_level.setFixedHeight(105)
        self.crd_select_level.setProperty("backgroundColor", "primary")
        self.crd_select_level.setProperty("border", "surface")
        self.crd_select_level.setProperty("borderRadiusVisible", True)

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
        lyt_inner_frame.addSpacing(10)
        lyt_inner_frame.addWidget(self.lbl_select_level)
        lyt_inner_frame.addWidget(self.frm_import_level)
        lyt_inner_frame.addWidget(self.crd_select_level)
        lyt_inner_frame.addStretch()
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
        self.lbl_header.setText(QCoreApplication.translate("NewProjectTypePage", "Open World", None))
        self.lbl_select_level.setText(QCoreApplication.translate("NewProjectTypePage", "Select World", None))
        self.btn_cancel.setText(QCoreApplication.translate("NewProjectTypePage", "Cancel", None))
        self.btn_back.setText(QCoreApplication.translate("NewProjectTypePage", "Back", None))
        self.btn_next.setText(QCoreApplication.translate("NewProjectTypePage", "Next", None))
        # fmt: on
