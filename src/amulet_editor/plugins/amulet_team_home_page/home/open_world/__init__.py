from amulet_editor import __version__

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from amulet_editor.data.build import get_resource
from ._open_world import Ui_OpenWorldPage


class OpenWorldPage(Ui_OpenWorldPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        back_icon = QIcon(get_resource("icons/tabler/arrow-left.svg")).pixmap(
            QSize(32, 32)
        )
        self.btn_back.setIcon(back_icon)
