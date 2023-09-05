# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, QEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from amulet_editor.models.widgets._toolbar import AToolBar
from amulet_team_main_window2._application.tab_engine import RecursiveSplitter


class Ui_AmuletMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("AmuletMainWindow")
        self.resize(1129, 792)

        self._widget = QWidget(self)
        self._widget.setObjectName("_widget")

        self._widget_layout = QVBoxLayout(self._widget)
        self._widget_layout.setSpacing(0)
        self._widget_layout.setObjectName("_widget_layout")
        self._widget_layout.setContentsMargins(0, 0, 0, 0)

        self._header_layout = QHBoxLayout()
        self._header_layout.setSpacing(0)
        self._header_layout.setObjectName("_header_layout")

        self.context_switch = QComboBox(self._widget)
        self.context_switch.setObjectName("context_switch")
        self._header_layout.addWidget(self.context_switch)

        self._header_spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self._header_layout.addItem(self._header_spacer)
        self._widget_layout.addLayout(self._header_layout)

        self._main_layout = QHBoxLayout()
        self._main_layout.setObjectName("_main_layout")

        self.toolbar = AToolBar(self._widget)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setFrameShape(QFrame.NoFrame)
        self.toolbar.setFrameShadow(QFrame.Raised)
        self.toolbar.setProperty("backgroundColor", "surface")
        self._main_layout.addWidget(self.toolbar)

        self.view_container = RecursiveSplitter(self._widget)
        self.view_container.setObjectName("view_container")
        self.view_container.setFrameShape(QFrame.StyledPanel)
        self.view_container.setFrameShadow(QFrame.Raised)
        self._main_layout.addWidget(self.view_container)
        self._main_layout.setStretch(1, 1)
        self._widget_layout.addLayout(self._main_layout)
        self._widget_layout.setStretch(1, 1)
        self.setCentralWidget(self._widget)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self):
        self.setWindowTitle(
            QCoreApplication.translate("AmuletMainWindow", "Amulet Editor", None)
        )
