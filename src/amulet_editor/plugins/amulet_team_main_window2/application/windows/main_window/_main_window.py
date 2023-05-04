from __future__ import annotations

from typing import Callable, Optional
from weakref import ref
import random

from PySide6.QtCore import QCoreApplication, QMetaObject, QEvent, Qt
from PySide6.QtGui import QIcon, QShortcut
from PySide6.QtWidgets import QMainWindow, QLabel

from amulet_team_inspector import show_inspector

from amulet_team_main_window2.application.widgets.tab_engine._tab_engine import (
    TabEngineStackedTabWidget,
    RecursiveSplitter,
    TabPage,
)


class CustomTabPage(QLabel, TabPage):
    def __init__(self):
        self._name = "Tab " + str(random.randint(1, 1000))
        super().__init__(self._name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon(self) -> Optional[QIcon]:
        return None


class AmuletMainWindow(QMainWindow):
    @staticmethod
    def _main_window() -> Optional[AmuletMainWindow]:
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if AmuletMainWindow._main_window() is not None:
            raise RuntimeError("An instance of AmuletMainWindow already exists")
        AmuletMainWindow._main_window = ref(self)

        if not self.objectName():
            self.setObjectName("AmuletMainWindow")
        self.resize(800, 600)

        self.splitter_widget = RecursiveSplitter()
        tw = TabEngineStackedTabWidget()
        for i in range(1, 5):
            tw.add_page(CustomTabPage())
        self.splitter_widget.addWidget(tw)
        # tw = TabEngineStackedTabWidget()
        # for i in range(10, 20):
        #     tw.add_page(CustomTabPage())
        # self.splitter_widget.addWidget(tw)
        self.setCentralWidget(self.splitter_widget)

        self.localise()
        QMetaObject.connectSlotsByName(self)

        f12 = QShortcut(Qt.Key.Key_F12, self)
        f12.activated.connect(show_inspector)

    @classmethod
    def main_window(cls) -> AmuletMainWindow:
        main_window: Optional[AmuletMainWindow] = cls._main_window()
        if main_window is None:
            raise RuntimeError("AmuletMainWindow instance does not exist.")
        return main_window

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self.localise()

    def localise(self):
        self.setWindowTitle(
            QCoreApplication.translate("AmuletMainWindow", "MainWindow", None)
        )
