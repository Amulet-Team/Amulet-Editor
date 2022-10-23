from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QMainWindow

if TYPE_CHECKING:
    from .plugin_api import AppPrivateAPI


class MainWindow(QMainWindow):
    def __init__(self, api: AppPrivateAPI):
        super().__init__()
