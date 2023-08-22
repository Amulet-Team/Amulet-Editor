# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_open_world.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_OpenWorldPage(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("OpenWorldPage")
        self.resize(264, 247)
        self.setProperty("backgroundColor", "background")

        self._vertical_layout = QVBoxLayout(self)
        self._vertical_layout.setSpacing(5)
        self._vertical_layout.setObjectName("_vertical_layout")
        self._vertical_layout.setContentsMargins(50, 50, 50, 50)

        self._lyt_header = QHBoxLayout()
        self._lyt_header.setObjectName("_lyt_header")

        self.btn_back = QPushButton(self)
        self.btn_back.setObjectName("btn_back")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_back.sizePolicy().hasHeightForWidth())
        self.btn_back.setSizePolicy(sizePolicy)
        self.btn_back.setMinimumSize(QSize(30, 30))
        self.btn_back.setMaximumSize(QSize(30, 30))
        self._lyt_header.addWidget(self.btn_back)

        self._lbl_title = QLabel(self)
        self._lbl_title.setObjectName("_lbl_title")
        self._lbl_title.setAlignment(Qt.AlignCenter)
        self._lyt_header.addWidget(self._lbl_title)

        self._horizontal_spacer = QSpacerItem(
            30, 30, QSizePolicy.Fixed, QSizePolicy.Minimum
        )
        self._lyt_header.addItem(self._horizontal_spacer)
        self._vertical_layout.addLayout(self._lyt_header)

        self.frame = QFrame(self)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.HLine)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setProperty("borderTop", "surface")
        self._vertical_layout.addWidget(self.frame)

        self._lbl_level_directory = QLabel(self)
        self._lbl_level_directory.setObjectName("_lbl_level_directory")
        self._lbl_level_directory.setProperty("color", "on_primary")
        self._vertical_layout.addWidget(self._lbl_level_directory)

        self._lyt_world_directory = QHBoxLayout()
        self._lyt_world_directory.setObjectName("_lyt_world_directory")

        self.lne_level_directory = QLineEdit(self)
        self.lne_level_directory.setObjectName("lne_level_directory")
        self.lne_level_directory.setMinimumSize(QSize(0, 25))
        self.lne_level_directory.setMaximumSize(QSize(16777215, 25))
        self.lne_level_directory.setReadOnly(True)
        self.lne_level_directory.setProperty("color", "on_surface")
        self._lyt_world_directory.addWidget(self.lne_level_directory)

        self.btn_level_directory = QPushButton(self)
        self.btn_level_directory.setObjectName("btn_level_directory")
        sizePolicy.setHeightForWidth(
            self.btn_level_directory.sizePolicy().hasHeightForWidth()
        )
        self.btn_level_directory.setSizePolicy(sizePolicy)
        self.btn_level_directory.setMinimumSize(QSize(27, 27))
        self.btn_level_directory.setMaximumSize(QSize(27, 27))
        self._lyt_world_directory.addWidget(self.btn_level_directory)
        self._vertical_layout.addLayout(self._lyt_world_directory)

        self._vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self._vertical_layout.addItem(self._vertical_spacer)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("OpenWorldPage", "Form", None))
        self.btn_back.setText("")
        self._lbl_title.setText(
            QCoreApplication.translate("OpenWorldPage", "Open World", None)
        )
        self._lbl_level_directory.setText(
            QCoreApplication.translate("OpenWorldPage", "World Directory", None)
        )
        self.btn_level_directory.setText("")
