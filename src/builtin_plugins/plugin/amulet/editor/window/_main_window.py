from __future__ import annotations
from threading import Lock

from PySide6.QtGui import QShortcut, QCloseEvent
from PySide6.QtCore import Qt, QEvent, QCoreApplication
from PySide6.QtWidgets import QWidget, QMainWindow, QHBoxLayout

from plugin.amulet.inspector import show_inspector

from plugin.amulet.editor._signal import destroy_editor
from plugin.amulet.editor.window._tab_engine import RecursiveSplitter
from plugin.amulet.editor.window._toolbar import ToolBar, ButtonProxy


# Terminology
# A Widget is an atomic GUI element within the program
# A Layout is an arrangement of widgets
# A tool button is a button in the toolbar. It can be configured to activate a layout or just run some code.

# A layout system.
#   controls where widgets are
#   Layout configurations are associated with identifiers
#   Layouts can be switched with code

# The lock must be acquired before reading/writing the objects below.
_lock = Lock()
_main_window: AmuletMainWindow | None = None


class AmuletMainWindow(QMainWindow):
    """
    The main window in the Amulet application.
    It contains a toolbar and a tab widget engine.
    """

    def __init__(self) -> None:
        super().__init__()
        self._widget = QWidget(self)
        self._layout = QHBoxLayout(self._widget)
        self._toolbar = ToolBar(self._widget)
        self._layout.addWidget(self._toolbar)

        self._view_container = RecursiveSplitter(self._widget)
        self._view_container.setObjectName("view_container")
        self._layout.addWidget(self._view_container)
        self.setCentralWidget(self._widget)

        self._localise()

        f12 = QShortcut(Qt.Key.Key_F12, self)
        f12.activated.connect(lambda: show_inspector(self))

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("AmuletMainWindow", "Amulet Editor", None)
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        global _main_window
        destroy_editor.emit()
        _main_window = None

    def replace_view_container(
        self, new_view_container: RecursiveSplitter
    ) -> RecursiveSplitter:
        old_view_container = self._view_container
        layout_item = self._layout.replaceWidget(
            old_view_container,
            new_view_container,
            options=Qt.FindChildOption.FindDirectChildrenOnly,
        )
        assert old_view_container is layout_item.widget()
        self._view_container = new_view_container
        return old_view_container


def init_main_window() -> None:
    global _main_window
    with _lock:
        if _main_window is not None:
            raise RuntimeError("AmuletMainWindow has already been initialised")
        _main_window = AmuletMainWindow()


def destroy_main_window() -> None:
    global _main_window
    with _lock:
        if _main_window is not None:
            _main_window.deleteLater()
            _main_window = None


def get_main_window() -> AmuletMainWindow:
    """Get the main window instance.
    This is a private function that must not be used outside of this plugin."""
    with _lock:
        if _main_window is None:
            raise RuntimeError("AmuletMainWindow has not been initialised.")
        return _main_window


def add_static_button() -> ButtonProxy:
    """
    Add an icon to the toolbar.

    :return: A ButtonProxy instance through which the button attributes can be set.
        You must store this somewhere in your plugin.
    """
    button = get_main_window()._toolbar.add_static_button()
    return ButtonProxy(button)
