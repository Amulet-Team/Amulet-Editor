# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_main_window_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget
from .toolbar import ToolBar
from amulet_team_editor.window._tab_engine import RecursiveSplitter


class Ui_AmuletMainWindow(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)
        if not self.objectName():
            self.setObjectName("AmuletMainWindow")
        self.resize(1129, 780)

        self._widget = QWidget(self)
        self._widget.setObjectName("_widget")

        self._layout = QHBoxLayout(self._widget)
        self._layout.setObjectName("_layout")

        self.toolbar = ToolBar(self._widget)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setProperty("backgroundColor", "surface")
        self._layout.addWidget(self.toolbar)

        self.view_container = RecursiveSplitter(self._widget)
        self.view_container.setObjectName("view_container")
        self._layout.addWidget(self.view_container)
        self.setCentralWidget(self._widget)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("AmuletMainWindow", "Amulet Editor", None)
        )
