# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_inspector.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.inspect_button = QPushButton(self)
        self.inspect_button.setObjectName("inspect_button")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inspect_button.sizePolicy().hasHeightForWidth()
        )
        self.inspect_button.setSizePolicy(sizePolicy)
        self.horizontalLayout_2.addWidget(self.inspect_button)

        self.reload_button = QPushButton(self)
        self.reload_button.setObjectName("reload_button")
        self.horizontalLayout_2.addWidget(self.reload_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

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
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.run_button.sizePolicy().hasHeightForWidth())
        self.run_button.setSizePolicy(sizePolicy1)
        self.horizontalLayout.addWidget(self.run_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(QCoreApplication.translate("InspectionTool", "Form", None))
        self.inspect_button.setText("")
        self.reload_button.setText("")
        self.run_button.setText(
            QCoreApplication.translate("InspectionTool", "Run", None)
        )
