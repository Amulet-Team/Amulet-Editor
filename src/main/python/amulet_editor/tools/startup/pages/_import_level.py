import os
import pathlib
from functools import partial

import amulet
from amulet_editor.data import build, minecraft
from amulet_editor.application.components import QElidedLabel
from amulet_editor.models.minecraft import LevelData
from amulet_editor.tools.startup._components import QIconButton
from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ImportLevelPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.level_directory = None

        self.setupUi()

        self.btn_import_level.clicked.connect(partial(self.select_level))

    def select_level(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Minecraft World",
            os.path.realpath(minecraft.save_directories()[0]),
            QFileDialog.ShowDirsOnly,
        )

        if os.path.exists(os.path.join(folder, "level.dat")):
            folder = str(os.path.sep).join(folder.split("/"))
            self.level_directory = folder
            self.lne_import_level.setText(folder)

            level_data = LevelData(amulet.load_format(folder))

            icon_path = (
                level_data.icon_path
                if level_data.icon_path is not None
                else build.get_resource("images/missing_world_icon.png")
            )
            level_icon = QPixmap(QImage(icon_path))
            level_icon = level_icon.scaledToHeight(80)

            level_name = level_data.name.get_html(font_weight=600)
            file_name = pathlib.PurePath(level_data.path).name
            version = f"{level_data.edition} - {level_data.version}"
            last_played = (
                level_data.last_played.astimezone(tz=None)
                .strftime("%B %d, %Y %I:%M %p")
                .replace(" 0", " ")
            )

            lbl_pixmap = QLabel(self.frm_level_data)
            lbl_pixmap.setPixmap(level_icon)
            lbl_pixmap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            lbl_pixmap.setProperty("border", "surface")
            lbl_pixmap.setProperty("borderRadiusVisible", True)

            lbl_level_name = QElidedLabel(level_name, parent=self.frm_level_data)
            lbl_level_name.setAttribute(Qt.WA_TransparentForMouseEvents)

            lbl_file_name = QElidedLabel(file_name, parent=self.frm_level_data)
            lbl_file_name.setAttribute(Qt.WA_TransparentForMouseEvents)

            lbl_version = QElidedLabel(version, parent=self.frm_level_data)
            lbl_version.setAttribute(Qt.WA_TransparentForMouseEvents)

            lbl_last_played = QElidedLabel(last_played, parent=self.frm_level_data)
            lbl_last_played.setAttribute(Qt.WA_TransparentForMouseEvents)

            lyt_frm_level_data: QGridLayout = self.frm_level_data.layout()
            lyt_frm_level_data.addWidget(lbl_pixmap, 0, 0, 4, 1)
            lyt_frm_level_data.addWidget(lbl_level_name, 0, 1, 1, 1)
            lyt_frm_level_data.addWidget(lbl_file_name, 1, 1, 1, 1)
            lyt_frm_level_data.addWidget(lbl_version, 2, 1, 1, 1)
            lyt_frm_level_data.addWidget(lbl_last_played, 3, 1, 1, 1)

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

        # 'Import Level' field
        self.lbl_select_level = QLabel(self.frm_inner_container)
        self.lbl_select_level.setProperty("color", "on_primary")

        lyt_import_level = QHBoxLayout(self.frm_inner_container)

        self.frm_select_level = QFrame(self.frm_inner_container)
        self.frm_select_level.setFrameShape(QFrame.NoFrame)
        self.frm_select_level.setFrameShadow(QFrame.Raised)
        self.frm_select_level.setLayout(lyt_import_level)

        self.lne_import_level = QLineEdit(self.frm_select_level)
        self.lne_import_level.setFixedHeight(25)
        self.lne_import_level.setProperty("color", "on_surface")
        self.lne_import_level.setReadOnly(True)

        self.btn_import_level = QIconButton(self.frm_select_level)
        self.btn_import_level.setFixedSize(QSize(27, 27))
        self.btn_import_level.setIcon("folder.svg")
        self.btn_import_level.setIconSize(QSize(15, 15))
        self.btn_import_level.setProperty("backgroundColor", "primary")

        lyt_import_level.addWidget(self.lne_import_level)
        lyt_import_level.addWidget(self.btn_import_level)
        lyt_import_level.setContentsMargins(0, 0, 0, 0)
        lyt_import_level.setSpacing(5)

        # Create 'Level Data' frame
        lyt_level_data = QGridLayout(self.frm_inner_container)

        self.frm_level_data = QFrame(self.frm_inner_container)
        self.frm_level_data.setFixedHeight(105)
        self.frm_level_data.setFrameShape(QFrame.NoFrame)
        self.frm_level_data.setFrameShadow(QFrame.Raised)
        self.frm_level_data.setLayout(lyt_level_data)
        self.frm_level_data.setProperty("backgroundColor", "primary")
        self.frm_level_data.setProperty("border", "surface")
        self.frm_level_data.setProperty("borderRadiusVisible", True)

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
        lyt_inner_frame.addWidget(self.frm_select_level)
        lyt_inner_frame.addWidget(self.frm_level_data)
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
        self.lbl_header.setText(QCoreApplication.translate("NewProjectTypePage", "Import World", None))
        self.lbl_select_level.setText(QCoreApplication.translate("NewProjectTypePage", "Select World", None))
        self.btn_cancel.setText(QCoreApplication.translate("NewProjectTypePage", "Cancel", None))
        self.btn_back.setText(QCoreApplication.translate("NewProjectTypePage", "Back", None))
        self.btn_next.setText(QCoreApplication.translate("NewProjectTypePage", "Next", None))
        # fmt: on
