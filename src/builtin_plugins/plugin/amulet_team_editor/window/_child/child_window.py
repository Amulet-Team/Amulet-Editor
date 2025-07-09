from PySide6.QtGui import QCloseEvent
from weakref import WeakSet

from .child_window_ui import Ui_AmuletChildWindow
from plugin.amulet_team_editor.window import _main as _main_window


class AmuletChildWindow(Ui_AmuletChildWindow):
    """The class for the sub-window.
    New instances must be constructed using create_sub_window."""

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
