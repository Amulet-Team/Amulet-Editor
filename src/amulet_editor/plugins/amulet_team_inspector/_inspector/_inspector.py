# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_inspector.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_InspectionTool(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("InspectionTool")
        self.resize(264, 247)
        self.setProperty("backgroundColor", "background")

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.reload_button = QPushButton(self)
        self.reload_button.setObjectName("reload_button")
        self.verticalLayout.addWidget(self.reload_button)

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setObjectName("tree_widget")
        self.tree_widget.header().setVisible(False)
        self.verticalLayout.addWidget(self.tree_widget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.code_editor = QPlainTextEdit(self)
        self.code_editor.setObjectName("code_editor")
        self.horizontalLayout.addWidget(self.code_editor)

        self.run_button = QPushButton(self)
        self.run_button.setObjectName("run_button")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.run_button.sizePolicy().hasHeightForWidth())
        self.run_button.setSizePolicy(sizePolicy)
        self.horizontalLayout.addWidget(self.run_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("InspectionTool", "Form", None))
        self.reload_button.setText(
            QCoreApplication.translate("InspectionTool", "Reload", None)
        )
        self.run_button.setText(
            QCoreApplication.translate("InspectionTool", "Run", None)
        )
