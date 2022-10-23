from __future__ import annotations

from PySide6.QtWidgets import QApplication

from .window import MainWindow
from .plugin_api import AppPrivateAPI


class App(QApplication):
    """The Qt App class"""

    def __init__(self):
        super().__init__()
        self.__api = AppPrivateAPI(self)
        self.__window = None

    def _init(self):
        self.__api.init()
        self.__window = MainWindow(self.__api)
        self.__window.show()

    def exec(self):
        self._init()
        super().exec()
