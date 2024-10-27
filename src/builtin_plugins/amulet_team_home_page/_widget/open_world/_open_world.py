# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file '_open_world.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_OpenWorldPage(QWidget):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        if not self.objectName():
            self.setObjectName("OpenWorldPage")
        self.resize(264, 247)
        self.setProperty("backgroundColor", "background")

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self._lyt_header = QHBoxLayout()
        self._lyt_header.setObjectName("_lyt_header")

        self.btn_back = QPushButton(self)
        self.btn_back.setObjectName("btn_back")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_back.sizePolicy().hasHeightForWidth())
        self.btn_back.setSizePolicy(sizePolicy)
        self.btn_back.setMinimumSize(QSize(30, 30))
        self.btn_back.setMaximumSize(QSize(30, 30))
        self._lyt_header.addWidget(self.btn_back)

        self._lbl_title = QLabel(self)
        self._lbl_title.setObjectName("_lbl_title")
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lyt_header.addWidget(self._lbl_title)

        self._horizontal_spacer = QSpacerItem(
            30, 30, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._lyt_header.addItem(self._horizontal_spacer)
        self.verticalLayout.addLayout(self._lyt_header)

        self.frame = QFrame(self)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.Shape.HLine)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setProperty("borderTop", "surface")
        self.verticalLayout.addWidget(self.frame)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.load_file_button = QPushButton(self)
        self.load_file_button.setObjectName("load_file_button")
        self.horizontalLayout.addWidget(self.load_file_button)

        self.load_directory_button = QPushButton(self)
        self.load_directory_button.setObjectName("load_directory_button")
        self.horizontalLayout.addWidget(self.load_directory_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self._vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(self._vertical_spacer)

        self._localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("OpenWorldPage", "Open World", None)
        )
        self.btn_back.setText("")
        self._lbl_title.setText(
            QCoreApplication.translate("OpenWorldPage", "open_level", None)
        )
        self.load_file_button.setText(
            QCoreApplication.translate("OpenWorldPage", "open_file", None)
        )
        self.load_directory_button.setText(
            QCoreApplication.translate("OpenWorldPage", "open_directory", None)
        )
