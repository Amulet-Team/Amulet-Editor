# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_home.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_HomePage(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("HomePage")
        self.resize(748, 788)

        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(5)
        self._layout.setObjectName("_layout")
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._left_spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self._layout.addItem(self._left_spacer)

        self._central_layout = QVBoxLayout()
        self._central_layout.setObjectName("_central_layout")
        self._central_layout.setContentsMargins(50, 50, 50, 50)

        self._top_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self._central_layout.addItem(self._top_spacer)

        self._lbl_app_icon = QLabel(self)
        self._lbl_app_icon.setObjectName("_lbl_app_icon")
        self._lbl_app_icon.setMinimumSize(QSize(0, 128))
        self._lbl_app_icon.setMaximumSize(QSize(16777215, 128))
        self._lbl_app_icon.setText("")
        self._lbl_app_icon.setAlignment(Qt.AlignCenter)
        self._central_layout.addWidget(self._lbl_app_icon)

        self._lbl_app_name = QLabel(self)
        self._lbl_app_name.setObjectName("_lbl_app_name")
        self._lbl_app_name.setAlignment(Qt.AlignCenter)
        self._lbl_app_name.setProperty("subfamily", "semi_light")
        self._lbl_app_name.setProperty("heading", "h1")
        self._central_layout.addWidget(self._lbl_app_name)

        self._lbl_app_version = QLabel(self)
        self._lbl_app_version.setObjectName("_lbl_app_version")
        self._lbl_app_version.setText("")
        self._lbl_app_version.setAlignment(Qt.AlignCenter)
        self._lbl_app_version.setProperty("color", "secondary")
        self._lbl_app_version.setProperty("heading", "h5")
        self._lbl_app_version.setProperty("subfamily", "semi_light")
        self._central_layout.addWidget(self._lbl_app_version)

        self._middel_spacer = QSpacerItem(
            20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._central_layout.addItem(self._middel_spacer)

        self._button_layout = QGridLayout()
        self._button_layout.setObjectName("_button_layout")

        self.btn_new_project = QPushButton(self)
        self.btn_new_project.setObjectName("btn_new_project")
        self.btn_new_project.setEnabled(False)
        self._button_layout.addWidget(self.btn_new_project, 1, 1, 1, 1)

        self._lbl_new_project = QLabel(self)
        self._lbl_new_project.setObjectName("_lbl_new_project")
        self._button_layout.addWidget(self._lbl_new_project, 1, 0, 1, 1)

        self._lbl_new_project_2 = QLabel(self)
        self._lbl_new_project_2.setObjectName("_lbl_new_project_2")
        self._button_layout.addWidget(self._lbl_new_project_2, 2, 0, 1, 1)

        self.btn_open_world = QPushButton(self)
        self.btn_open_world.setObjectName("btn_open_world")
        self._button_layout.addWidget(self.btn_open_world, 0, 1, 1, 1)

        self.cbo_language = QComboBox(self)
        self.cbo_language.setObjectName("cbo_language")
        self._button_layout.addWidget(self.cbo_language, 3, 0, 1, 2)

        self._lbl_open_level = QLabel(self)
        self._lbl_open_level.setObjectName("_lbl_open_level")
        self._button_layout.addWidget(self._lbl_open_level, 0, 0, 1, 1)

        self.btn_open_project = QPushButton(self)
        self.btn_open_project.setObjectName("btn_open_project")
        self.btn_open_project.setEnabled(False)
        self._button_layout.addWidget(self.btn_open_project, 2, 1, 1, 1)
        self._button_layout.setColumnStretch(0, 1)
        self._central_layout.addLayout(self._button_layout)

        self._bottom_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self._central_layout.addItem(self._bottom_spacer)
        self._layout.addLayout(self._central_layout)

        self._right_spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self._layout.addItem(self._right_spacer)

        self._quick_access = QWidget(self)
        self._quick_access.setObjectName("_quick_access")
        self._layout.addWidget(self._quick_access)
        self._layout.setStretch(0, 1)
        self._layout.setStretch(2, 1)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("HomePage", "Form", None))
        self._lbl_app_name.setText(
            QCoreApplication.translate("HomePage", "amulet_editor", None)
        )
        self.btn_new_project.setText(
            QCoreApplication.translate("HomePage", "btn_create_project", None)
        )
        self._lbl_new_project.setText(
            QCoreApplication.translate("HomePage", "lbl_create_project", None)
        )
        self._lbl_new_project_2.setText(
            QCoreApplication.translate("HomePage", "lbl_open_project", None)
        )
        self.btn_open_world.setText(
            QCoreApplication.translate("HomePage", "btn_open_level", None)
        )
        self._lbl_open_level.setText(
            QCoreApplication.translate("HomePage", "lbl_open_level", None)
        )
        self.btn_open_project.setText(
            QCoreApplication.translate("HomePage", "btn_open_project", None)
        )
