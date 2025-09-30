from weakref import WeakSet

from PySide6.QtCore import Qt, QEvent, QCoreApplication
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QWidget


from . import _main_window
from . import _tab_widget


class AmuletChildWindow(QMainWindow):
    """
    The class for the sub-window.
    New instances must be constructed using create_sub_window.
    """

    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)
        self._splitter = _tab_widget.RecursiveSplitter()
        self.setCentralWidget(self._splitter)
        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("AmuletChildWindow", "Amulet Editor", None)
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        # The parent keeps this object alive. We need to do this so it can be destroyed
        self.setParent(None)
        self.deleteLater()


# This can only be modified from the main thread.
sub_windows = WeakSet[AmuletChildWindow]()


def create_sub_window() -> AmuletChildWindow:
    """Create a new sub-window.
    The main window owns the sub-window and a weak reference is stored in sub_windows.
    """
    window = AmuletChildWindow(_main_window.get_main_window())
    sub_windows.add(window)
    return window
