# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '_home.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("HomePage")
        self.resize(1129, 945)

        self._vertical_layout = QVBoxLayout(self)
        self._vertical_layout.setSpacing(5)
        self._vertical_layout.setObjectName("_vertical_layout")
        self._vertical_layout.setContentsMargins(50, 50, 50, 50)

        self.lbl_app_icon = QLabel(self)
        self.lbl_app_icon.setObjectName("lbl_app_icon")
        self.lbl_app_icon.setMinimumSize(QSize(0, 128))
        self.lbl_app_icon.setMaximumSize(QSize(16777215, 128))
        self.lbl_app_icon.setText("")
        self.lbl_app_icon.setAlignment(Qt.AlignCenter)
        self._vertical_layout.addWidget(self.lbl_app_icon)

        self.lbl_app_name = QLabel(self)
        self.lbl_app_name.setObjectName("lbl_app_name")
        self.lbl_app_name.setAlignment(Qt.AlignCenter)
        self.lbl_app_name.setProperty("subfamily", "semi_light")
        self.lbl_app_name.setProperty("heading", "h1")
        self._vertical_layout.addWidget(self.lbl_app_name)

        self.lbl_app_version = QLabel(self)
        self.lbl_app_version.setObjectName("lbl_app_version")
        self.lbl_app_version.setText("")
        self.lbl_app_version.setAlignment(Qt.AlignCenter)
        self.lbl_app_version.setProperty("color", "secondary")
        self.lbl_app_version.setProperty("heading", "h5")
        self.lbl_app_version.setProperty("subfamily", "semi_light")
        self._vertical_layout.addWidget(self.lbl_app_version)
        self._vertical_spacer = QSpacerItem(
            20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._vertical_layout.addItem(self._vertical_spacer)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.btn_new_project = QPushButton(self)
        self.btn_new_project.setObjectName("btn_new_project")
        self.btn_new_project.setEnabled(False)
        self.gridLayout.addWidget(self.btn_new_project, 1, 1, 1, 1)

        self.label_2 = QLabel(self)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.label_3 = QLabel(self)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.btn_open_world = QPushButton(self)
        self.btn_open_world.setObjectName("btn_open_world")
        self.gridLayout.addWidget(self.btn_open_world, 0, 1, 1, 1)

        self.cbo_language = QComboBox(self)
        self.cbo_language.setObjectName("cbo_language")
        self.gridLayout.addWidget(self.cbo_language, 3, 0, 1, 2)

        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.btn_open_project = QPushButton(self)
        self.btn_open_project.setObjectName("btn_open_project")
        self.btn_open_project.setEnabled(False)
        self.gridLayout.addWidget(self.btn_open_project, 2, 1, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self._vertical_layout.addLayout(self.gridLayout)

        self.localise()

        QMetaObject.connectSlotsByName(self)

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("HomePage", "Form", None))
        self.lbl_app_name.setText(
            QCoreApplication.translate("HomePage", "Amulet Editor", None)
        )
        self.btn_new_project.setText(
            QCoreApplication.translate("HomePage", "New Project", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("HomePage", "Create a new project", None)
        )
        self.label_3.setText(
            QCoreApplication.translate("HomePage", "Open an existing project", None)
        )
        self.btn_open_world.setText(
            QCoreApplication.translate("HomePage", "Open Level", None)
        )
        self.label.setText(
            QCoreApplication.translate("HomePage", "Open an existing level", None)
        )
        self.btn_open_project.setText(
            QCoreApplication.translate("HomePage", "Open Project", None)
        )
