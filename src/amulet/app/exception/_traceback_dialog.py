from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QWidget

from ._traceback_dialog_gui import TracebackDialogGUI
from amulet.app.resource import get_resource_path


class TracebackDialog(TracebackDialogGUI):
    """A dialog to display tracebacks."""

    def __init__(
        self,
        parent: QWidget | None = None,
        f: Qt.WindowType = Qt.WindowType.Widget,
        title: str = "",
        error: str = "",
        traceback: str = "",
    ) -> None:
        super().__init__(parent, f)
        self._traceback = traceback
        alert_icon = QIcon(get_resource_path("icons/tabler/alert-circle.svg")).pixmap(
            QSize(32, 32)
        )
        self._alert_image.setPixmap(alert_icon)
        self._copy_button.clicked.connect(self._on_copy)
        self.setWindowTitle(title)
        self._error_text.setText(error)
        self._traceback_text.setText(traceback)

    def _on_copy(self) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._traceback)
