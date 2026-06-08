from __future__ import annotations

import logging
from weakref import WeakMethod, WeakSet

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QShowEvent, QHideEvent

from amulet.level.abc import Level

from .._layout import LayoutConfig, SplitterConfig, WidgetStackConfig, get_layout
from ..widget._widget import get_dock_widget_constructor, dock_widget_registered
from ..widget._missing import MissingWidget, MissingTabIdentifier

from ._child_window import DockChildWindow
from ._tab_widget import TabWidgetStack, RecursiveSplitter, TabWidgetMeta
from ._overlay import DropArea

log = logging.getLogger(__name__)


class DockMainWidget(QWidget):
    def __init__(self, level: Level, layout_name: str) -> None:
        super().__init__()
        self._level = level
        self._layout_name = layout_name

        self._child_windows = WeakSet[DockChildWindow]()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._widget: TabWidgetStack | RecursiveSplitter | None = None

        self._initialised = False

        dock_widget_registered.connect(self._populate_widgets)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if not self._initialised:
            self._initialised = True
            self._create_layout(get_layout(self._layout_name))

        for window in self._child_windows:
            window.show()

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        for window in self._child_windows:
            window.hide()

    def _create_child_window(
        self, widget: TabWidgetStack | RecursiveSplitter
    ) -> DockChildWindow:
        window = DockChildWindow(self, widget)
        self._child_windows.add(window)
        return window

    def _bind_events(self, widget: TabWidgetStack | RecursiveSplitter) -> None:
        log.debug(f"DockMainWidget._bind_events({widget})")
        if isinstance(widget, TabWidgetStack):
            widget.split.connect(self._on_split)
        else:
            widget.penultimate_child_removed.connect(self._on_penultimate_child_removed)

    def _unbind_events(self, widget: TabWidgetStack | RecursiveSplitter) -> None:
        log.debug(f"DockMainWidget._unbind_events({widget})")
        if isinstance(widget, TabWidgetStack):
            widget.split.disconnect(self._on_split)
        else:
            widget.penultimate_child_removed.disconnect(
                self._on_penultimate_child_removed
            )

    def _on_penultimate_child_removed(self) -> None:
        log.debug(f"DockMainWidget._on_penultimate_child_removed()")
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
        log.debug(f"DockMainWidget._on_split()")
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
    ) -> TabWidgetStack | RecursiveSplitter | None:
        old_widget = self._widget
        if old_widget is not None:
            self._unbind_events(old_widget)
            self._layout.removeWidget(old_widget)
        self._layout.addWidget(new_widget)
        self._bind_events(new_widget)
        self._widget = new_widget
        return old_widget

    def _init_layout(
        self,
        layout: SplitterConfig | WidgetStackConfig,
    ) -> TabWidgetStack | RecursiveSplitter:
        if isinstance(layout, SplitterConfig):
            splitter_widget = RecursiveSplitter()
            splitter_widget.setOrientation(layout.orientation)
            splitter_widget.addWidget(self._init_layout(layout.first))
            splitter_widget.addWidget(self._init_layout(layout.second))
            left_weight = max(1, min(100, int(100 * layout.weight)))
            right_weight = 100 - left_weight
            splitter_widget.setStretchFactor(0, left_weight)
            splitter_widget.setStretchFactor(1, right_weight)
            return splitter_widget
        elif isinstance(layout, WidgetStackConfig):
            _create_child_window = WeakMethod(self._create_child_window)

            def create_child_window(
                child_tab_widget: TabWidgetStack,
            ) -> DockChildWindow | None:
                func = _create_child_window()
                if func is None:
                    return None
                return func(child_tab_widget)

            tab_widget = TabWidgetStack(create_child_window)
            for widget_config in layout.widgets:
                try:
                    widget_cls = get_dock_widget_constructor(widget_config.identifier)
                except KeyError:
                    tab_widget_meta = TabWidgetMeta(
                        MissingTabIdentifier,
                        MissingWidget(widget_config.identifier),
                    )
                else:
                    tab_widget_meta = TabWidgetMeta(
                        widget_config.identifier, widget_cls(self._level)
                    )

                tab_widget._add_tab_widget(tab_widget_meta)
            return tab_widget
        else:
            raise RuntimeError(f"Unknown layout type {type(layout)}")

    def _create_layout(self, layout_config: LayoutConfig) -> None:
        """Initialisation of the layout."""
        # TODO: set window position and size
        old_widget = self._replace_widget(
            self._init_layout(layout_config.main_window.layout)
        )
        if old_widget is not None:
            old_widget.deleteLater()
        for config in layout_config.sub_windows:
            self._create_child_window(
                self._init_layout(config.layout),
            )

    def _populate_widgets(self, widget_identifier: str) -> None:
        """Populate all missing widgets of this type.
        If a widget is created before its plugin is loaded, it will be a missing widget.
        This function replaces all missing widgets with the real widget."""
        widget_constructor = get_dock_widget_constructor(widget_identifier)
        level = self._level
        if isinstance(self._widget, (TabWidgetStack, RecursiveSplitter)):
            self._widget.populate_widgets(
                widget_identifier, lambda: widget_constructor(level)
            )
        for child_window in self._child_windows:
            child_window.populate_widgets(
                widget_identifier, lambda: widget_constructor(level)
            )
