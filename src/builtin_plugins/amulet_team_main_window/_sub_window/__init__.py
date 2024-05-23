from PySide6.QtGui import QCloseEvent
from weakref import WeakSet

from .sub_window import Ui_AmuletSubWindow
from .. import _main_window as main_window


class AmuletSubWindow(Ui_AmuletSubWindow):
    """The class for the sub-window.
    New instances must be constructed using create_sub_window."""

    def closeEvent(self, event: QCloseEvent) -> None:
        # The parent keeps this object alive. We need to do this so it can be destroyed
        self.setParent(None)
        self.deleteLater()


# This can only be modified from the main thread.
sub_windows = WeakSet[AmuletSubWindow]()


def create_sub_window() -> AmuletSubWindow:
    """Create a new sub-window.
    The main window owns the sub-window and a weak reference is stored in sub_windows."""
    window = AmuletSubWindow(main_window.get_main_window())
    sub_windows.add(window)
    return window
