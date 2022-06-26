# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_explorer_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class Ui_ExplorerPanel(object):
    def setupUi(self, ExplorerPanel):
        if not ExplorerPanel.objectName():
            ExplorerPanel.setObjectName(u"ExplorerPanel")
        ExplorerPanel.resize(300, 480)
        self.verticalLayout = QVBoxLayout(ExplorerPanel)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frm_directory = QFrame(ExplorerPanel)
        self.frm_directory.setObjectName(u"frm_directory")
        self.frm_directory.setMinimumSize(QSize(0, 24))
        self.frm_directory.setFrameShape(QFrame.NoFrame)
        self.frm_directory.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frm_directory)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)

        self.verticalLayout.addWidget(self.frm_directory)

        self.trv_directory = QTreeView(ExplorerPanel)
        self.trv_directory.setObjectName(u"trv_directory")
        self.trv_directory.setFrameShape(QFrame.NoFrame)
        self.trv_directory.setIndentation(8)
        self.trv_directory.setUniformRowHeights(True)
        self.trv_directory.setHeaderHidden(True)
        self.trv_directory.header().setVisible(False)

        self.verticalLayout.addWidget(self.trv_directory)

        self.retranslateUi(ExplorerPanel)

        QMetaObject.connectSlotsByName(ExplorerPanel)

    # setupUi

    def retranslateUi(self, ExplorerPanel):
        ExplorerPanel.setWindowTitle(
            QCoreApplication.translate("ExplorerPanel", u"Form", None)
        )

    # retranslateUi
