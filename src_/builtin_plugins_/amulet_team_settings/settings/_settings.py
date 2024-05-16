# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_SettingsPage(QWidget):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        if not self.objectName():
            self.setObjectName("SettingsPage")
        self.resize(748, 788)

        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self._central_layout = QVBoxLayout()
        self._central_layout.setObjectName("_central_layout")
        self._central_layout.setContentsMargins(50, 50, 50, 50)

        self.label = QLabel(self)
        self.label.setObjectName("label")
        self._central_layout.addWidget(self.label)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self._central_layout.addItem(self.verticalSpacer)
        self.horizontalLayout.addLayout(self._central_layout)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayout.addItem(self.horizontalSpacer)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(2, 1)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(QCoreApplication.translate("SettingsPage", "Form", None))
        self.label.setText(QCoreApplication.translate("SettingsPage", "Settings", None))
