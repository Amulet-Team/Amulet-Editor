from PySide6.QtCore import Slot, QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon

from ._traceback_dialog import Ui_AmuletTracebackDialog
from amulet_editor.data.build import get_resource


class _AmuletTracebackDialog(Ui_AmuletTracebackDialog):
    """A dialog to display tracebacks."""

    def __init__(
        self,
        parent=None,
        f=Qt.WindowType.Widget,
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
