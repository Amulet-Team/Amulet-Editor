from amulet_editor import __version__

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from amulet_editor.data import build
from ._home import Ui_HomePage


class HomePage(Ui_HomePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        amulet_logo = QPixmap(QImage(build.get_resource("images/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)
        self.lbl_app_icon.setPixmap(amulet_logo)
        self.lbl_app_version.setText(f"Version {__version__}")
        self._central_layout.setAlignment(Qt.AlignCenter)
        self.cbo_language.addItem("English")
