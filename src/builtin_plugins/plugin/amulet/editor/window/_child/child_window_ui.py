# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file 'child_window_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import QMainWindow, QWidget
from plugin.amulet.editor.window._tab_engine import RecursiveSplitter


class Ui_AmuletChildWindow(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)
        if not self.objectName():
            self.setObjectName("AmuletChildWindow")
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
            QCoreApplication.translate("AmuletChildWindow", "Amulet Editor", None)
        )
