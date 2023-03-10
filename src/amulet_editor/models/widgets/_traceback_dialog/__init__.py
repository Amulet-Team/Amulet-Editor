import traceback

from PySide6.QtCore import Slot, Qt, QSize
from PySide6.QtGui import QGuiApplication, QIcon

from ._traceback_dialog import Ui_AmuletTracebackDialog
from amulet_editor.data.build import get_resource


class AmuletTracebackDialog(Ui_AmuletTracebackDialog):
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
        alert_icon = QIcon(get_resource("icons/tabler/alert-circle.svg")).pixmap(
            QSize(32, 32)
        )
        self._alert_image.setPixmap(alert_icon)
        self._copy_button.clicked.connect(self._on_copy)
        self.setWindowTitle(title)
        self._error_text.setText(error)
        self._traceback_text.setText(traceback)

    @Slot()
    def _on_copy(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._traceback)


class DisplayException:
    """A class to catch exceptions and display the traceback dialog."""

    def __init__(self, msg: str):
        self._msg = msg

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            dialog = AmuletTracebackDialog(
                title=self._msg,
                error=str(exc_val),
                traceback="".join(traceback.format_tb(exc_tb)),
            )
            dialog.exec()
        return False
