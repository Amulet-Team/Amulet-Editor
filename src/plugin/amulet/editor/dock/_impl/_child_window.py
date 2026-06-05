from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QWidget

from . import _tab_widget
from . import _tab_drag

log = logging.getLogger(__name__)


class DockChildWindow(QMainWindow):
    """
    The class for the sub-window.
    New instances must be constructed using create_sub_window.
    """

    _widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter

    def __init__(
        self,
        parent: QWidget,
        widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter,
    ) -> None:
        super().__init__(parent)
        self._widget = widget
        self._bind_events(self._widget)
        self.setCentralWidget(self._widget)

    def _bind_events(
        self, widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    ) -> None:
        log.debug(f"DockChildWindow._bind_events({self}, {widget})")
        if isinstance(widget, _tab_widget.TabWidgetStack):
            widget.last_tab_removed.connect(self._on_last_tab_closed)
            widget.split.connect(self._on_split)
        else:
            widget.penultimate_child_removed.connect(self._on_penultimate_child_removed)

    def _unbind_events(
        self, widget: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    ) -> None:
        log.debug(f"DockChildWindow._unbind_events({self}, {widget})")
        if isinstance(widget, _tab_widget.TabWidgetStack):
            widget.last_tab_removed.disconnect(self._on_last_tab_closed)
            widget.split.disconnect(self._on_split)
        else:
            widget.penultimate_child_removed.disconnect(
                self._on_penultimate_child_removed
            )

    def _on_last_tab_closed(self, _: _tab_widget.TabWidgetStack) -> None:
        log.debug(f"DockChildWindow._on_last_tab_closed({self})")
        self.close()

    def _on_penultimate_child_removed(self) -> None:
        log.debug(f"DockChildWindow._on_penultiate_child_removed({self})")
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
            self._bind_events(new_widget)

            # Add the new widget
            self._widget = new_widget
            self._bind_events(new_widget)
            self.setCentralWidget(new_widget)

    def _on_split(
        self,
        old_widget: _tab_widget.TabWidgetStack,
        new_widget: _tab_widget.TabWidgetStack,
        direction: _tab_drag.DropArea,
    ) -> None:
        log.debug(f"DockChildWindow._on_split({self}, {new_widget}, {direction})")
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
            self.setCentralWidget(splitter)

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

    def closeEvent(self, event: QCloseEvent) -> None:
        # The parent keeps this object alive. We need to do this so it can be destroyed
        self.setParent(None)
        self.deleteLater()
