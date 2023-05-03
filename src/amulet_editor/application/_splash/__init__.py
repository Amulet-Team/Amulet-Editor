from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QPixmap

from amulet_editor.data.build import get_resource

from ._splash import Ui_Splash


class Splash(Ui_Splash):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self._logo.setPixmap(QPixmap(get_resource("icons/amulet/Icon.ico")))
        self.setWindowTitle("Amulet Editor")

    def showMessage(self, msg: str):
        self._msg.setText(msg)
        QCoreApplication.processEvents()
