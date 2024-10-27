# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_splash.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget


class Ui_Splash(QDialog):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Dialog
    ) -> None:
        super().__init__(parent, f)
        if not self.objectName():
            self.setObjectName("Splash")
        self.resize(400, 300)

        self._layout = QVBoxLayout(self)
        self._layout.setObjectName("_layout")

        self._logo = QLabel(self)
        self._logo.setObjectName("_logo")
        self._logo.setText("")
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._logo)

        self._msg = QLabel(self)
        self._msg.setObjectName("_msg")
        self._msg.setText("")
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._msg)
        self._layout.setStretch(0, 1)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(QCoreApplication.translate("Splash", "Amulet Editor", None))
