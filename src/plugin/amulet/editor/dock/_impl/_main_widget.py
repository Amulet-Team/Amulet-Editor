from __future__ import annotations

import logging
from weakref import WeakMethod, WeakSet

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QShowEvent, QHideEvent

from ._child_window import DockChildWindow
from ._tab_widget import TabWidgetStack, RecursiveSplitter
from ._overlay import DropArea

log = logging.getLogger(__name__)


class DockMainWidget(QWidget):
    def __init__(self, layout_name: str) -> None:
        super().__init__()
        self._child_windows = WeakSet[DockChildWindow]()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._widget: TabWidgetStack | RecursiveSplitter = RecursiveSplitter()
        self._bind_events(self._widget)
        self._layout.addWidget(self._widget)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        for window in self._child_windows:
            window.show()

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        for window in self._child_windows:
            window.hide()

    def _create_child_window(self, widget: TabWidgetStack) -> DockChildWindow:
        window = DockChildWindow(self, widget)
        self._child_windows.add(window)
        return window

    def _bind_events(self, widget: TabWidgetStack | RecursiveSplitter) -> None:
        log.debug(f"AmuletMainWindow._bind_events({widget})")
        if isinstance(widget, TabWidgetStack):
            widget.split.connect(self._on_split)
        else:
            widget.penultimate_child_removed.connect(self._on_penultimate_child_removed)

    def _unbind_events(self, widget: TabWidgetStack | RecursiveSplitter) -> None:
        log.debug(f"AmuletMainWindow._unbind_events({widget})")
        if isinstance(widget, TabWidgetStack):
            widget.split.disconnect(self._on_split)
        else:
            widget.penultimate_child_removed.disconnect(
                self._on_penultimate_child_removed
            )

    def _on_penultimate_child_removed(self) -> None:
        log.debug(f"AmuletMainWindow._on_penultimate_child_removed()")
        # Switch from a splitter to a stack
        if isinstance(self._widget, RecursiveSplitter):
            old_widget = self._widget
            new_widget = old_widget.remove_index(0)
            if not isinstance(new_widget, (TabWidgetStack, RecursiveSplitter)):
                raise TypeError()

            # Remove the old widget
            self._unbind_events(old_widget)

            # Add the new widget
            self._widget = new_widget
            self._bind_events(new_widget)
            self._layout.addWidget(new_widget)
            old_widget.deleteLater()

    def _on_split(
        self,
        old_widget: TabWidgetStack,
        new_widget: TabWidgetStack,
        direction: DropArea,
    ) -> None:
        log.debug(f"AmuletMainWindow._on_split()")
        # Switch from a stack to a splitter
        if isinstance(self._widget, TabWidgetStack):
            # Remove the old widget
            assert old_widget is self._widget
            self._unbind_events(old_widget)
            old_widget.setParent(None)

            is_vertical = direction in (
                DropArea.Top,
                DropArea.Bottom,
            )
            is_last = direction in (DropArea.Right, DropArea.Bottom)
            size = (old_widget.height() if is_vertical else old_widget.width()) // 2

            # Create the new widget
            self._widget = splitter = RecursiveSplitter()
            self._bind_events(splitter)
            self._layout.removeWidget(old_widget)
            self._layout.addWidget(splitter)

            # Put the widgets in the splitter
            splitter.setOrientation(
                Qt.Orientation.Vertical if is_vertical else Qt.Orientation.Horizontal
            )
            splitter.addWidget(old_widget)
            splitter.insertWidget(int(is_last), new_widget)

            splitter.setSizes([size, size])

            assert old_widget.parent() is splitter
            assert new_widget.parent() is splitter
            assert splitter.parent() is self

    def _replace_widget(
        self, new_widget: TabWidgetStack | RecursiveSplitter
    ) -> TabWidgetStack | RecursiveSplitter:
        old_widget = self._widget
        self._unbind_events(old_widget)
        self._layout.removeWidget(old_widget)
        self._layout.addWidget(new_widget)
        self._bind_events(new_widget)
        self._widget = new_widget
        return old_widget
