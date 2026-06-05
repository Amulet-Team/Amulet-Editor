"""Widgets that make up the recursive tab framework."""

from __future__ import annotations

from typing import Callable
from weakref import ref
import logging

from PySide6.QtCore import Qt, QSize, QEvent, QObject, QTimer, Signal
from PySide6.QtGui import (
    QWheelEvent,
    QCursor,
    QHoverEvent,
    QEnterEvent,
    QShowEvent,
    QResizeEvent,
    QIcon,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QStackedWidget,
    QHBoxLayout,
    QButtonGroup,
    QScrollArea,
    QFrame,
    QLabel,
)

from amulet.app.qt.signal import TypeFormSignal

from plugin.amulet.editor.dock.widget import DockWidget

from . import _tab_drag

log = logging.getLogger(__name__)


class TabButton(QPushButton):
    pass


class TabWidgetMeta:
    # The identifier for the stored widget class
    identifier: str

    # The tab displayed in the tab bar
    tab: TabButton

    # The TabWidget instance
    widget: DockWidget

    # The callable bound to the tab click signal
    tab_click_event: Callable[[], None] | None

    # The drag manager bound to the tab
    tab_drag_manager: _tab_drag.TabDragManager | None

    # A callable that returns the TabWidgetStack the TabWidget is bound to.
    bound_widget: Callable[[], TabWidgetStack | None]

    def __init__(self, identifier: str, tab_widget: DockWidget) -> None:
        self.identifier = identifier
        self.tab = TabButton(tab_widget.icon, tab_widget.title)
        self.tab.setCheckable(True)
        tab_widget.title_changed.connect(self._on_title_change)
        tab_widget.icon_changed.connect(self._on_icon_change)
        self.widget = tab_widget
        self.tab_click_event = None
        self.tab_drag_manager = None
        self.bound_widget = lambda: None

    def _on_title_change(self, title: str) -> None:
        self.tab.setText(title)

    def _on_icon_change(self, icon: QIcon | None) -> None:
        if icon is None:
            self.tab.setIcon(QIcon())
        else:
            self.tab.setIcon(icon)


class TabContainerWidget(QWidget):
    """Subclass of QWidget so it can be found in the hierarchy."""

    pass


class HorizontalScrollableTabArea(QScrollArea):
    """
    A horizontal scrollable area.
    This a specialisation of QScrollArea that:
        hides scroll bars,
        handles widget resizing.
        handles enter and leave events when scrolling,
    Use :meth:`child_layout` like a normal QHBoxLayout and this will handle the rest.
    """

    def __init__(self) -> None:
        super().__init__()
        self._widget = TabContainerWidget()

        self._layout = QHBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._child_widget = QWidget()
        self._layout.addWidget(self._child_widget)

        self._child_layout = QHBoxLayout(self._child_widget)
        self._child_layout.setContentsMargins(0, 0, 0, 0)
        self._child_layout.setSpacing(0)

        self._layout.addStretch(1)

        # Disable scroll area rendering
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidget(self._widget)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        # Listen for child resizing
        self._child_widget.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._child_widget and isinstance(event, QResizeEvent):
            self.child_size_change.emit()
        return False

    def child_widget(self) -> QWidget:
        return self._child_widget

    def child_layout(self) -> QHBoxLayout:
        """The layout the owner should interact with."""
        return self._child_layout

    child_size_change = Signal()

    def scroll_left(self) -> None:
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 60)

    def scroll_right(self) -> None:
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 60)

    def sizeHint(self) -> QSize:
        return QSize(0, self._child_layout.sizeHint().height())

    def minimumSizeHint(self, /) -> QSize:
        return QSize(0, self._child_layout.sizeHint().height())

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Enter and leave events are not generated automatically when scrolling.
        # This manually generates them.

        # Store which widget the mouse is over
        global_pos = QCursor.pos()
        old_pos = self._widget.mapFromGlobal(global_pos)
        old_widget = QApplication.widgetAt(global_pos)

        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - event.angleDelta().y() // 5)

        # Get the new widget the mouse is over
        new_widget = QApplication.widgetAt(QCursor.pos())
        # If the mouse is over a different widget manually generate the leave and enter events.
        # Qt does not generate them automatically for some reason.
        if old_widget != new_widget:
            new_pos = self._widget.mapFromGlobal(global_pos)
            if old_widget is not None:
                QApplication.sendEvent(old_widget, QEvent(QEvent.Type.Leave))
                QApplication.sendEvent(
                    old_widget,
                    QHoverEvent(
                        QEvent.Type.HoverLeave,
                        new_pos,
                        global_pos,
                        old_pos,
                        Qt.KeyboardModifier.NoModifier,
                    ),
                )
            if new_widget is not None:
                QApplication.sendEvent(
                    new_widget,
                    QEnterEvent(
                        new_pos,
                        new_pos,
                        global_pos,
                    ),
                )
                QApplication.sendEvent(
                    new_widget,
                    QHoverEvent(QEvent.Type.HoverEnter, new_pos, global_pos, old_pos),
                )


class TemporaryNewTabWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(QLabel("This is a placeholder new tab GUI."))


class WidgetStack(QStackedWidget):
    pass


class TabWidgetStack(QWidget):
    """A custom class that behaves like a QTabWidget"""

    def __init__(
        self, create_child_window: Callable[[TabWidgetStack], QMainWindow | None]
    ) -> None:
        super().__init__()
        self._create_child_window = create_child_window
        self.setAcceptDrops(True)

        # Convert from the button to the storage class
        self._tabs = dict[QWidget, TabWidgetMeta]()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._tab_bar_meta_layout = QHBoxLayout()
        self._tab_bar_meta_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_bar_meta_layout.setSpacing(0)
        self._layout.addLayout(self._tab_bar_meta_layout)

        self._button_group = QButtonGroup()
        self._button_group.setExclusive(True)

        self._plus_button = QPushButton("+")
        self._plus_button.setCheckable(True)
        self._button_group.addButton(self._plus_button)
        self._tab_bar_meta_layout.addWidget(self._plus_button)
        self._plus_button.setFixedWidth(self._plus_button.sizeHint().height())

        self._tab_container = HorizontalScrollableTabArea()
        self._tab_bar_meta_layout.addWidget(self._tab_container)
        self._tab_bar_layout = self._tab_container.child_layout()

        self._left_button = QPushButton("<")
        self._tab_bar_meta_layout.addWidget(self._left_button)
        self._left_button.clicked.connect(self._tab_container.scroll_left)
        self._left_button.setFixedWidth(self._left_button.sizeHint().height())

        self._right_button = QPushButton(">")
        self._tab_bar_meta_layout.addWidget(self._right_button)
        self._right_button.clicked.connect(self._tab_container.scroll_right)
        self._right_button.setFixedWidth(self._right_button.sizeHint().height())

        self._stacked_widget = WidgetStack()
        self._layout.addWidget(self._stacked_widget, 1)

        self._new_tab_widget = TemporaryNewTabWidget()
        self._stacked_widget.addWidget(self._new_tab_widget)
        self._plus_button.clicked.connect(
            lambda: self._stacked_widget.setCurrentWidget(self._new_tab_widget)
        )

        self._tab_container.child_size_change.connect(self._on_resize)

    # Emitted when the stack is empty (the stack will still have the default add widget)
    last_tab_removed = TypeFormSignal("TabWidgetStack")

    split = TypeFormSignal("TabWidgetStack", "TabWidgetStack", _tab_drag.DropArea)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # Make sure a widget is visible
        if self._button_group.checkedButton() is None:
            for i in range(self._tab_bar_layout.count(), -1, -1):
                item = self._tab_bar_layout.itemAt(i)
                if item is None:
                    continue
                widget = item.widget()
                if not isinstance(widget, QPushButton):
                    continue
                widget.click()

                # Delay call resize handler.
                # For some reason calling this directly does not work.
                QTimer.singleShot(50, self._on_resize)

                break
            else:
                self._plus_button.click()

    def _set_arrow_visibility(self, tab_container_width: int, tab_width: int) -> None:
        """
        tab_container_width: The visible tab width
        tab_width: The full width of the tabs
        """
        if not self._left_button.isVisible():
            tab_container_width -= self._left_button.width()
        if not self._right_button.isVisible():
            tab_container_width -= self._right_button.width()
        if tab_width <= tab_container_width:
            self._left_button.hide()
            self._right_button.hide()
        else:
            self._left_button.show()
            self._right_button.show()

    def _ensure_tab_visible(self) -> None:
        button = self._button_group.checkedButton()
        if button is None or button is self._plus_button:
            return
        self._tab_container.ensureWidgetVisible(button, 0, 0)

    def _on_resize(self) -> None:
        self._set_arrow_visibility(
            self._tab_container.width(), self._tab_container.child_widget().width()
        )
        self._ensure_tab_visible()

    def resizeEvent(self, event: QResizeEvent, /) -> None:
        self._on_resize()
        super().resizeEvent(event)

    def _insert_tab_widget(self, index: int, tab_widget_meta: TabWidgetMeta) -> None:
        """Insert a TabWidget instance to this stack."""
        if tab_widget_meta.bound_widget() is not None:
            raise RuntimeError(
                "TabWidget has not been removed from previous TabWidgetStack"
            )

        tab = tab_widget_meta.tab
        widget = tab_widget_meta.widget

        self._button_group.addButton(tab)
        self._tabs[tab] = tab_widget_meta
        self._tab_bar_layout.insertWidget(index, tab)

        self._stacked_widget.addWidget(widget)

        self_ref = ref(self)

        def on_click() -> None:
            if self_ := self_ref():
                self_._tab_container.ensureWidgetVisible(tab, 0, 0)
                self_._stacked_widget.setCurrentWidget(widget)

        drag_manager = _tab_drag.TabDragManager(
            self, tab_widget_meta, self._create_child_window
        )
        tab.installEventFilter(drag_manager)

        tab.clicked.connect(on_click)
        tab_widget_meta.tab_click_event = on_click
        tab_widget_meta.tab_drag_manager = drag_manager
        tab_widget_meta.bound_widget = self_ref

    def _add_tab_widget(self, tab_widget: TabWidgetMeta) -> None:
        """Append a TabWidget instance to this stack."""
        self._insert_tab_widget(-1, tab_widget)

    def _steal_tab_widget(self, tab_widget_meta: TabWidgetMeta) -> None:
        """Remove the tab and widget but do not remove the drag event listener."""
        if tab_widget_meta.bound_widget() is not self:
            raise RuntimeError("TabWidget is not bound to this TabWidgetStack")

        tab = tab_widget_meta.tab
        widget = tab_widget_meta.widget

        del self._tabs[tab]

        if tab is self._button_group.checkedButton():
            # Find another tab to enable
            tabs = self._get_tabs()
            try:
                i = tabs.index(tab)
            except ValueError:
                i = -1
            if i <= 0:
                if i + 1 < len(tabs):
                    tabs[i + 1].click()
                else:
                    self._plus_button.click()
            else:
                tabs[i - 1].click()

        self._tab_bar_layout.removeWidget(tab)
        tab.setParent(None)
        self._stacked_widget.removeWidget(widget)
        widget.setParent(None)

        if tab_widget_meta.tab_click_event is not None:
            tab.clicked.disconnect(tab_widget_meta.tab_click_event)
            tab_widget_meta.tab_click_event = None

        self._button_group.removeButton(tab)

    def _disconnect_tab_widget(
        self, tab_widget_meta: TabWidgetMeta, cleanup: bool = True
    ) -> None:
        if tab_widget_meta.tab_drag_manager is not None:
            tab_widget_meta.tab.removeEventFilter(tab_widget_meta.tab_drag_manager)
            tab_widget_meta.tab_drag_manager = None
        tab_widget_meta.bound_widget = lambda: None
        if cleanup and not self._tabs:
            self.last_tab_removed.emit(self)

    def _remove_tab_widget(self, tab_widget_meta: TabWidgetMeta) -> None:
        """
        Remove a TabWidget instance from this stack.
        This also removes all functionality
        """
        self._steal_tab_widget(tab_widget_meta)
        self._disconnect_tab_widget(tab_widget_meta)

    def _replace_widget(
        self, tab_widget_meta_old: TabWidgetMeta, tab_widget_meta_new: TabWidgetMeta
    ) -> None:
        """Replace the tab widget with another"""
        # Find the old tab index
        i = self._get_tab_widgets().index(tab_widget_meta_old)

        # insert the new tab
        self._insert_tab_widget(i, tab_widget_meta_new)

        # Activate the new tab if the old one was active
        if self._button_group.checkedButton() is tab_widget_meta_old.tab:
            tab_widget_meta_new.tab.click()

        # Remove the old widget
        self._remove_tab_widget(tab_widget_meta_old)

    def _is_empty(self) -> bool:
        return not self._tabs

    def _get_tabs(self) -> list[QPushButton]:
        tabs = []
        for i in range(self._tab_bar_layout.count()):
            item = self._tab_bar_layout.itemAt(i)
            if item is not None:
                tab = item.widget()
                if isinstance(tab, QPushButton):
                    tabs.append(tab)
        return tabs

    def _get_tab_widgets(self) -> list[TabWidgetMeta]:
        """
        Get all the TabWidget instances in this stack.
        They are ordered based on the order in the tab bar.
        """
        tab_widgets = []
        for tab in self._get_tabs():
            tab_widget = self._tabs.get(tab)
            if tab_widget is not None:
                tab_widgets.append(tab_widget)
        return tab_widgets


def get_tab_widget_stack(widget: QWidget) -> TabWidgetStack:
    """Get the TabWidgetStack that contains this widget."""
    widget_: QObject | None = widget
    while widget_ is not None:
        if isinstance(widget_, TabWidgetStack):
            return widget_
        widget_ = widget_.parent()
    raise RuntimeError(f"{widget} is not in a TabWidgetStack")


class RecursiveSplitter(QSplitter):
    """A specialisation of QSplitter"""

    def __init__(self) -> None:
        super().__init__()
        self.setChildrenCollapsible(False)
        self._children: list[QWidget] = []

    # Emitted when the penultimate child is removed
    penultimate_child_removed = TypeFormSignal("RecursiveSplitter")

    def _on_last_tab_removed(self, stack: TabWidgetStack) -> None:
        log.debug(f"RecursiveSplitter._on_last_tab_removed({self}, {stack})")
        self.remove_widget(stack).deleteLater()

    def _on_split(
        self,
        old_widget: TabWidgetStack,
        new_widget: TabWidgetStack,
        direction: _tab_drag.DropArea,
    ) -> None:
        log.debug(
            f"RecursiveSplitter._on_split({self}, {old_widget}, {new_widget}, {direction})"
        )

        self_sizes = self.sizes()

        index = self.indexOf(old_widget)
        splitter = RecursiveSplitter()
        if old_widget is not self.replaceWidget(index, splitter):
            raise RuntimeError()

        assert splitter.parent() is self

        is_vertical = direction in (_tab_drag.DropArea.Top, _tab_drag.DropArea.Bottom)
        is_last = direction in (_tab_drag.DropArea.Right, _tab_drag.DropArea.Bottom)
        size = (old_widget.height() if is_vertical else old_widget.width()) // 2

        # Put the widgets in the splitter
        splitter.setOrientation(
            Qt.Orientation.Vertical if is_vertical else Qt.Orientation.Horizontal
        )
        splitter.addWidget(old_widget)
        splitter.insertWidget(int(is_last), new_widget)

        self.setSizes(self_sizes)
        splitter.setSizes([size, size])

        assert old_widget.parent() is splitter
        assert new_widget.parent() is splitter
        assert splitter.parent() is self

    def _on_sub_penultimate_child_removed(self, splitter: RecursiveSplitter) -> None:
        """The penultimate child of a child splitter was removed. Replace the splitter with its child."""
        log.debug(
            f"RecursiveSplitter._on_sub_penultimate_child_removed({self}, {splitter})"
        )
        sizes = self.sizes()
        child = splitter.remove_index(0)
        index = self.indexOf(splitter)
        self.insertWidget(index, child)
        self.remove_widget(splitter).deleteLater()
        self.setSizes(sizes)

    def _bind_events(self, widget: QWidget) -> None:
        log.debug(f"RecursiveSplitter._bind_events({self}, {widget})")
        if isinstance(widget, RecursiveSplitter):
            widget.penultimate_child_removed.connect(
                self._on_sub_penultimate_child_removed
            )
        elif isinstance(widget, TabWidgetStack):
            widget.last_tab_removed.connect(self._on_last_tab_removed)
            widget.split.connect(self._on_split)

    def _unbind_events(self, widget: QWidget) -> None:
        log.debug(f"RecursiveSplitter._unbind_events({self}, {widget})")
        if isinstance(widget, RecursiveSplitter):
            widget.penultimate_child_removed.disconnect(
                self._on_sub_penultimate_child_removed
            )
        elif isinstance(widget, TabWidgetStack):
            widget.last_tab_removed.disconnect(self._on_last_tab_removed)
            widget.split.disconnect(self._on_split)

    def addWidget(self, widget: QWidget, /) -> None:
        log.debug(f"RecursiveSplitter.addWidget({self}, {widget})")
        super().addWidget(widget)
        self._bind_events(widget)
        self._children.append(widget)

    def insertWidget(self, index: int, widget: QWidget, /) -> None:
        log.debug(f"RecursiveSplitter.insertWidget({self}, {index}, {widget})")
        super().insertWidget(index, widget)
        self._bind_events(widget)
        self._children.append(widget)

    def replaceWidget(self, index: int, widget: QWidget, /) -> QWidget:
        log.debug(f"RecursiveSplitter.replaceWidget({self}, {index}, {widget})")
        old_widget = super().replaceWidget(index, widget)
        if old_widget is None:
            raise RuntimeError(f"There is no widget at index {index}")
        self._unbind_events(old_widget)
        self._bind_events(widget)
        self._children.remove(old_widget)
        self._children.append(widget)
        return old_widget

    def remove_widget(self, widget: QWidget, /) -> QWidget:
        """Hide and orphan the widget."""
        log.debug(f"RecursiveSplitter.remove_widget({self}, {widget})")
        self._children.remove(widget)
        widget.setParent(None)
        self._unbind_events(widget)
        if self.count() == 1:
            # Notify the listener that there is only one child left
            self.penultimate_child_removed.emit(self)
        return widget

    def remove_index(self, index: int, /) -> QWidget:
        """Hide and orphan the widget at the given index."""
        log.debug(f"RecursiveSplitter.remove_index({self}, {index}, {self})")
        widget = self.widget(index)
        if widget is None:
            raise RuntimeError(f"There is no widget at index {index}")
        return self.remove_widget(widget)
