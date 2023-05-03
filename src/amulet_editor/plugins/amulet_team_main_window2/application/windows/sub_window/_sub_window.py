from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QEvent
from PySide6.QtWidgets import QMainWindow

import amulet_team_main_window2.application.widgets.tab_engine._tab_engine as tab_engine


class AmuletSubWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.objectName():
            self.setObjectName("AmuletSubWindow")
        self.resize(800, 600)

        self.splitter_widget = tab_engine.RecursiveSplitter()
        tw = tab_engine.TabEngineStackedTabWidget()
        self.splitter_widget.addWidget(tw)
        self.setCentralWidget(self.splitter_widget)

        self.localise()
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(
            QCoreApplication.translate("AmuletSubWindow", "SubWindow", None)
        )
