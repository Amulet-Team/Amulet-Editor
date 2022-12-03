from __future__ import annotations
from amulet_editor_plugin_test.plugin import Plugin
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
import sys


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(198, 42)
        self.centralwidget = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.pushButton = QPushButton(parent=self.centralwidget, text="sys.modules")
        self.pushButton.clicked.connect(self._print_sys_modules)
        self.verticalLayout.addWidget(self.pushButton)
        self.setCentralWidget(self.centralwidget)

    @Slot()
    def _print_sys_modules(self):
        print(sorted(sys.modules.keys(), key=lambda k: k.lower()))


class TestPlugin(Plugin):
    def on_load(self):
        self._window = TestWindow()
        self._window.show()

    def on_unload(self):
        self._window.deleteLater()
        self._window = None
