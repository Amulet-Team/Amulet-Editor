# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_landing_window.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget
from amulet_editor.models.widgets._toolbar import AToolBar


class Ui_AmuletLandingWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("AmuletLandingWindow")
        self.resize(800, 600)

        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")

        self.horizontalLayout = QHBoxLayout(self.central_widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = AToolBar(self.central_widget)
        self.toolbar.setObjectName("toolbar")
        self.horizontalLayout.addWidget(self.toolbar)

        self.tool_widget = QStackedWidget(self.central_widget)
        self.tool_widget.setObjectName("tool_widget")
        self.horizontalLayout.addWidget(self.tool_widget)
        self.setCentralWidget(self.central_widget)

        self.localise()
        self.tool_widget.setCurrentIndex(-1)
        QMetaObject.connectSlotsByName(self)

    def localise(self):
        self.setWindowTitle(
            QCoreApplication.translate("AmuletLandingWindow", "MainWindow", None)
        )
