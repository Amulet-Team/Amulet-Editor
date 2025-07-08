# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_inspector.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class Ui_InspectionTool(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)
        if not self.objectName():
            self.setObjectName("InspectionTool")
        self.resize(266, 252)

        self._central_widget = QWidget(self)
        self._central_widget.setObjectName("_central_widget")

        self._vertical_layout = QVBoxLayout(self._central_widget)
        self._vertical_layout.setObjectName("_vertical_layout")

        self._horizontal_layout_2 = QHBoxLayout()
        self._horizontal_layout_2.setObjectName("_horizontal_layout_2")

        self.inspect_button = QPushButton(self._central_widget)
        self.inspect_button.setObjectName("inspect_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inspect_button.sizePolicy().hasHeightForWidth()
        )
        self.inspect_button.setSizePolicy(sizePolicy)
        self._horizontal_layout_2.addWidget(self.inspect_button)

        self.reload_button = QPushButton(self._central_widget)
        self.reload_button.setObjectName("reload_button")
        self._horizontal_layout_2.addWidget(self.reload_button)
        self._vertical_layout.addLayout(self._horizontal_layout_2)

        self.tree_widget = QTreeWidget(self._central_widget)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, "1")
        self.tree_widget.setHeaderItem(__qtreewidgetitem)
        self.tree_widget.setObjectName("tree_widget")
        self.tree_widget.header().setVisible(False)
        self._vertical_layout.addWidget(self.tree_widget)

        self._horizontal_layout_1 = QHBoxLayout()
        self._horizontal_layout_1.setObjectName("_horizontal_layout_1")

        self.code_editor = QPlainTextEdit(self._central_widget)
        self.code_editor.setObjectName("code_editor")
        self._horizontal_layout_1.addWidget(self.code_editor)

        self.run_button = QPushButton(self._central_widget)
        self.run_button.setObjectName("run_button")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.run_button.sizePolicy().hasHeightForWidth())
        self.run_button.setSizePolicy(sizePolicy1)
        self._horizontal_layout_1.addWidget(self.run_button)
        self._vertical_layout.addLayout(self._horizontal_layout_1)
        self.setCentralWidget(self._central_widget)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("InspectionTool", "Inspector", None)
        )
        self.inspect_button.setText("")
        self.reload_button.setText("")
        self.run_button.setText(
            QCoreApplication.translate("InspectionTool", "Run", None)
        )
