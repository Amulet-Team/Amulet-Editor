# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file 'sub_window.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import QMainWindow, QWidget
from amulet_team_main_window2._application.tab_engine import RecursiveSplitter


class Ui_AmuletSubWindow(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, f)
        if not self.objectName():
            self.setObjectName("AmuletSubWindow")
        self.resize(1129, 792)

        self.view_container = RecursiveSplitter(self)
        self.view_container.setObjectName("view_container")
        self.setCentralWidget(self.view_container)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("AmuletSubWindow", "Amulet Editor", None)
        )
