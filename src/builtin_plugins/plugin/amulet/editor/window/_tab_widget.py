"""Widgets that make up the recursive tab framework."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QSize, QEvent, QObject, QTimer
from PySide6.QtGui import (
    QWheelEvent,
    QCursor,
    QHoverEvent,
    QEnterEvent,
    QShowEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QApplication,
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

from amulet.app.qt.signal import Signal

from plugin.amulet.editor.widget.abc import TabWidget


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

    child_size_change = Signal[()]()

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


class TabData:
    click_event: Callable[[], None] | None
    drag_manager: TabDragManager

    def __init__(
        self, click_event: Callable[[], None], drag_manager: TabDragManager
    ) -> None:
        self.click_event = click_event
        self.drag_manager = drag_manager


def get_tab_data(tab_widget: TabWidget) -> TabData | None:
    return tab_widget._private_tab_data


def set_tab_data(tab_widget: TabWidget, data: TabData | None) -> None:
    tab_widget._private_tab_data = data


class TabWidgetStack(QWidget):
    """A custom class that behaves like a QTabWidget"""

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)

        # Convert from the button to the storage class
        self._tabs = dict[QWidget, TabWidget]()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

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

        self._stacked_widget = QStackedWidget()
        self._layout.addWidget(self._stacked_widget, 1)

        self._new_tab_widget = TemporaryNewTabWidget()
        self._stacked_widget.addWidget(self._new_tab_widget)
        self._plus_button.clicked.connect(
            lambda: self._stacked_widget.setCurrentWidget(self._new_tab_widget)
        )

        self._tab_container.child_size_change.connect(self._on_resize)

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

    def _add_tab_widget(self, tab_widget: TabWidget) -> None:
        """Add a TabWidget instance to this stack."""
        if get_tab_data(tab_widget) is not None:
            raise RuntimeError(
                "TabWidget has not been removed from previous TabWidgetStack"
            )

        tab = tab_widget.tab
        self._button_group.addButton(tab)
        self._tabs[tab] = tab_widget
        self._tab_bar_layout.addWidget(tab)

        widget = tab_widget.widget
        self._stacked_widget.addWidget(widget)

        def on_click() -> None:
            self._tab_container.ensureWidgetVisible(tab, 0, 0)
            self._stacked_widget.setCurrentWidget(widget)

        drag_manager = TabDragManager(tab_widget)
        tab.installEventFilter(drag_manager)

        tab.clicked.connect(on_click)
        set_tab_data(tab_widget, TabData(on_click, drag_manager))

    def _steal_tab_widget(self, tab_widget: TabWidget) -> None:
        """Remove the tab and widget but do not remove the drag event listener."""
        tab_data = get_tab_data(tab_widget)
        if tab_data is None:
            raise RuntimeError("TabWidget is not in this TabWidgetStack")

        tab = tab_widget.tab
        widget = tab_widget.widget

        del self._tabs[tab]

        self._tab_bar_layout.removeWidget(tab)
        tab.setParent(None)
        self._stacked_widget.removeWidget(widget)
        widget.setParent(None)

        if tab_data.click_event is not None:
            tab.clicked.disconnect(tab_data.click_event)
            tab_data.click_event = None

        self._button_group.removeButton(tab)

    def _remove_tab_widget(self, tab_widget: TabWidget) -> None:
        """
        Remove a TabWidget instance from this stack.
        This also removes all functionality
        """
        self._steal_tab_widget(tab_widget)
        tab_data = get_tab_data(tab_widget)
        if tab_data is None:
            raise RuntimeError("TabWidget is not in this TabWidgetStack")
        tab_widget.tab.removeEventFilter(tab_data.drag_manager)
        set_tab_data(tab_widget, None)

    def _get_tabs(self) -> list[QPushButton]:
        tabs = []
        for i in range(self._tab_bar_layout.count()):
            item = self._tab_bar_layout.itemAt(i)
            if item is not None:
                tab = item.widget()
                if isinstance(tab, QPushButton):
                    tabs.append(tab)
        return tabs

    def _get_tab_widgets(self) -> list[TabWidget]:
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


from ._tab_drag import TabDragManager
