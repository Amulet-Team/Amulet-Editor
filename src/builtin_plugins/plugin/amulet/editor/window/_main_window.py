from __future__ import annotations
from threading import Lock
import logging

from PySide6.QtGui import QCloseEvent, QAction
from PySide6.QtCore import Qt, QEvent, QCoreApplication
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QBoxLayout,
    QHBoxLayout,
    QVBoxLayout,
    QMenu,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from plugin.amulet.inspector import show_inspector

from plugin.amulet.editor._signal import destroy_editor
from plugin.amulet.level import get_main_level

from . import _tab_widget
from . import _tab_drag
from ._toolbar import ToolBar, ButtonProxy

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

log = logging.getLogger(__name__)


def save_level() -> None:
    level = get_main_level()
    if level is not None:
        # TODO: add some kind of dialog for the user to see
        level.save()


class AmuletMainWindow(QMainWindow):
    """
    The main window in the Amulet application.
    It contains a toolbar and a tab widget engine.
    """

    _widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    _save_action: QAction | None

    def __init__(self) -> None:
        super().__init__()

        self._file_menu = QMenu()

        if get_main_level() is not None:
            self._save_action = QAction(self, autoRepeat=False)
            self._save_action.triggered.connect(save_level)
            self._file_menu.addAction(self._save_action)
        else:
            self._save_action = None

        self.menuBar().addMenu(self._file_menu)

        self._tool_menu = QMenu()

        self._inspect_action = QAction(self, autoRepeat=False)
        self._inspect_action.triggered.connect(self._show_inspector)
        self._tool_menu.addAction(self._inspect_action)

        self.menuBar().addMenu(self._tool_menu)

        # TODO: make this configurable
        orientation: QBoxLayout.Direction = QBoxLayout.Direction.LeftToRight

        self._central_widget = QWidget(self)
        self._central_layout = QBoxLayout(orientation, self._central_widget)
        self._central_layout.setContentsMargins(2, 2, 2, 2)
        self._central_layout.setSpacing(2)

        self._toolbar = ToolBar(
            Qt.Orientation.Vertical
            if orientation == QBoxLayout.Direction.LeftToRight
            or orientation == QBoxLayout.Direction.RightToLeft
            else Qt.Orientation.Horizontal
        )
        self._central_layout.addWidget(self._toolbar)

        self._widget_layout = QVBoxLayout()
        self._central_layout.addLayout(self._widget_layout, 1)

        self._widget = _tab_widget.RecursiveSplitter()
        self._bind_events(self._widget)
        self._widget_layout.addWidget(self._widget)

        self.setCentralWidget(self._central_widget)

        # This is here to stop the window closing and reopening when the first QOpenGLWidget is added.
        self._dummy_gl_widget = QOpenGLWidget(self)
        self._dummy_gl_widget.hide()

        self._localise()

    def _bind_events(
        self, widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    ) -> None:
        log.debug(f"AmuletMainWindow._bind_events({widget})")
        if isinstance(widget, _tab_widget.TabWidgetStack):
            widget.split.connect(self._on_split)
        else:
            widget.penultimate_child_removed.connect(self._on_penultimate_child_removed)

    def _unbind_events(
        self, widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    ) -> None:
        log.debug(f"AmuletMainWindow._unbind_events({widget})")
        if isinstance(widget, _tab_widget.TabWidgetStack):
            widget.split.disconnect(self._on_split)
        else:
            widget.penultimate_child_removed.disconnect(
                self._on_penultimate_child_removed
            )

    def _on_penultimate_child_removed(self) -> None:
        log.debug(f"AmuletMainWindow._on_penultimate_child_removed()")
        # Switch from a splitter to a stack
        if isinstance(self._widget, _tab_widget.RecursiveSplitter):
            old_widget = self._widget
            new_widget = old_widget.remove_index(0)
            if not isinstance(
                new_widget, (_tab_widget.TabWidgetStack, _tab_widget.RecursiveSplitter)
            ):
                raise TypeError()

            # Remove the old widget
            self._unbind_events(old_widget)

            # Add the new widget
            self._widget = new_widget
            self._bind_events(new_widget)
            self._widget_layout.addWidget(new_widget)
            old_widget.deleteLater()

    def _on_split(
        self,
        old_widget: _tab_widget.TabWidgetStack,
        new_widget: _tab_widget.TabWidgetStack,
        direction: _tab_drag.DropArea,
    ) -> None:
        log.debug(f"AmuletMainWindow._on_split()")
        # Switch from a stack to a splitter
        if isinstance(self._widget, _tab_widget.TabWidgetStack):
            # Remove the old widget
            assert old_widget is self._widget
            self._unbind_events(old_widget)
            old_widget.setParent(None)

            is_vertical = direction in (
                _tab_drag.DropArea.Top,
                _tab_drag.DropArea.Bottom,
            )
            is_last = direction in (_tab_drag.DropArea.Right, _tab_drag.DropArea.Bottom)
            size = (old_widget.height() if is_vertical else old_widget.width()) // 2

            # Create the new widget
            self._widget = splitter = _tab_widget.RecursiveSplitter()
            self._bind_events(splitter)
            self._widget_layout.removeWidget(old_widget)
            self._widget_layout.addWidget(splitter)

            # Put the widgets in the splitter
            splitter.setOrientation(
                Qt.Orientation.Vertical if is_vertical else Qt.Orientation.Horizontal
            )
            splitter.addWidget(old_widget)
            splitter.insertWidget(int(is_last), new_widget)

            splitter.setSizes([size, size])

            assert old_widget.parent() is splitter
            assert new_widget.parent() is splitter
            assert splitter.parent() is self._central_widget

    def _replace_widget(
        self, new_widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    ) -> _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter:
        old_widget = self._widget
        self._unbind_events(old_widget)
        self._widget_layout.removeWidget(old_widget)
        self._widget_layout.addWidget(new_widget)
        self._bind_events(new_widget)
        self._widget = new_widget
        return old_widget

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate(
                "plugin.amulet.editor.AmuletMainWindow",
                "amulet_editor",
                None,
            )
        )
        self._file_menu.setTitle(
            QCoreApplication.translate(
                "plugin.amulet.editor.AmuletMainWindow",
                "file_menu_text",
                None,
            )
        )
        if self._save_action is not None:
            self._save_action.setText(
                QCoreApplication.translate(
                    "plugin.amulet.editor.AmuletMainWindow",
                    "save_action_text",
                    None,
                )
            )
            self._save_action.setShortcut(
                QCoreApplication.translate(
                    "plugin.amulet.editor.AmuletMainWindow",
                    "save_action_shortcut",
                    None,
                )
            )
        self._tool_menu.setTitle(
            QCoreApplication.translate(
                "plugin.amulet.editor.AmuletMainWindow",
                "tool_menu_text",
                None,
            )
        )
        self._inspect_action.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.AmuletMainWindow",
                "inspect_action_text",
                None,
            )
        )
        self._inspect_action.setShortcut(
            QCoreApplication.translate(
                "plugin.amulet.editor.AmuletMainWindow",
                "inspect_action_shortcut",
                None,
            )
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        global _main_window
        destroy_editor.emit()
        _main_window = None

    def _show_inspector(self) -> None:
        show_inspector(self)


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
