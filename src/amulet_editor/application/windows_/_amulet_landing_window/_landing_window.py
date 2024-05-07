# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_landing_window.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QWidget
from amulet_editor.application.windows._amulet_landing_window._view import ViewContainer
from amulet_editor.models.widgets._toolbar import AToolBar


class Ui_AmuletLandingWindow(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)
        if not self.objectName():
            self.setObjectName("AmuletLandingWindow")
        self.resize(800, 600)

        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")

        self.horizontalLayout = QHBoxLayout(self.central_widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self._toolbar = AToolBar(self.central_widget)
        self._toolbar.setObjectName("_toolbar")
        self._toolbar.setFrameShape(QFrame.Shape.NoFrame)
        self._toolbar.setFrameShadow(QFrame.Shadow.Raised)
        self._toolbar.setProperty("backgroundColor", "surface")
        self.horizontalLayout.addWidget(self._toolbar)

        self._view_container = ViewContainer(self.central_widget)
        self._view_container.setObjectName("_view_container")
        self.horizontalLayout.addWidget(self._view_container)
        self.horizontalLayout.setStretch(1, 1)
        self.setCentralWidget(self.central_widget)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("AmuletLandingWindow", "MainWindow", None)
        )
