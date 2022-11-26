from amulet_editor import __version__

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from amulet_editor.data import build
from ._open_world import OpenWorldPage as _OpenWorldPage


class OpenWorldPage(_OpenWorldPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        back_icon = QPixmap(QImage(build.get_resource("icons/tabler/arrow-left.svg")))
        # back_icon = back_icon.scaledToHeight(30)
        self.btn_back.setIcon(back_icon)
