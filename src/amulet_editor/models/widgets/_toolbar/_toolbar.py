# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_toolbar.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
from amulet_editor.models.widgets import ADragContainer


class Ui_AToolBar(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("AToolBar")
        self.resize(829, 720)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self._wgt_dynamic_tools = ADragContainer(self)
        self._wgt_dynamic_tools.setObjectName("_wgt_dynamic_tools")
        self.verticalLayout.addWidget(self._wgt_dynamic_tools)

        self._lyt_fixed_tools = QVBoxLayout()
        self._lyt_fixed_tools.setObjectName("_lyt_fixed_tools")

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self._lyt_fixed_tools.addItem(self.verticalSpacer)
        self.verticalLayout.addLayout(self._lyt_fixed_tools)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("AToolBar", "Form", None))
