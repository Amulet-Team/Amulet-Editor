from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QPixmap, QGuiApplication

from ._traceback_dialog import Ui_TracebackDialog
from amulet_editor.data.build import get_resource


class TracebackDialog(Ui_TracebackDialog):
    def __init__(
        self,
        parent=None,
        f=Qt.WindowFlags(),
        title: str = "",
        error: str = "",
        traceback: str = "",
    ):
        super().__init__(parent, f)
        self._traceback = traceback
        # alert_icon = QPixmap(QImage(get_resource("icons/tabler/alert-circle.svg"))).scaledToHeight(32)
        alert_icon = QPixmap(
            get_resource("icons/tabler/alert-circle.svg")
        ).scaledToHeight(32)
        self._alert_image.setPixmap(alert_icon)
        self._copy_button.clicked.connect(self._on_copy)
        self.setWindowTitle(title)
        self._error_text.setText(error)
        self._traceback_text.setText(traceback)

    @Slot()
    def _on_copy(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._traceback)
