from typing import Callable
import traceback
from weakref import finalize, WeakMethod

from PySide6.QtCore import QSize, Qt, QObject, QEvent, QPoint, QRect
from PySide6.QtGui import (
    QMouseEvent,
    QResizeEvent,
    QWheelEvent,
    QCursor,
    QHoverEvent,
    QEnterEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QWidget,
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QButtonGroup,
    QScrollArea,
    QPushButton,
    QApplication,
)

from amulet.app.qt.signal import Signal
from amulet.app.exception import display_exception

from plugin.amulet.editor._toolbar_button import ToolbarButton


class ButtonProxy:
    """
    This class is a proxy for a button in the toolbar.
    This is returned by the constructor for the button.
    You must store a reference to this in your plugin otherwise the button will be deleted.
    This is also used to access and remove the button.
    """

    def __init__(self, button: ToolbarButton) -> None:
        """
        :param button: The button to wrap.
        """
        self._button: ToolbarButton | None = button
        self._on_click: Callable[[], None] | None = None

    def _get_button(self) -> ToolbarButton:
        if self._button is None:
            raise RuntimeError("The button has already been destroyed.")
        return self._button

    def set_icon(self, icon_path: str) -> None:
        self._get_button().setIcon(icon_path)

    def set_name(self, name: str) -> None:
        self._get_button().setToolTip(name)

    def set_callback(self, callback: Callable[[], None] | None = None) -> None:
        def on_click() -> None:
            if callback is not None:
                try:
                    callback()
                except Exception as e:
                    display_exception(
                        title=f"Error running {callback}",
                        error=str(e),
                        traceback=traceback.format_exc(),
                    )

        button = self._get_button()
        if self._on_click is not None:
            button.clicked.disconnect(self._on_click)
        self._on_click = on_click
        button.clicked.connect(on_click)

    def click(self) -> None:
        self._get_button().click()


ButtonSize = 40
IconSize = 30

LayoutCls: dict[Qt.Orientation, type[QVBoxLayout | QHBoxLayout]] = {
    Qt.Orientation.Vertical: QVBoxLayout,
    Qt.Orientation.Horizontal: QHBoxLayout,
}


class DynamicButtonWidget(QScrollArea):
    """A rearrangeable list of buttons."""

    resized = Signal[()]()
    _widgets_moved = Signal[()]()

    def __init__(
        self,
        parent: QWidget | None = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
    ):
        super().__init__(parent)
        self._orientation = orientation

        if orientation == Qt.Orientation.Vertical:
            self._size_hint = QSize(ButtonSize, ButtonSize * 2)
        else:
            self._size_hint = QSize(ButtonSize * 2, ButtonSize)

        self._widget = QWidget()

        layout_cls = LayoutCls[orientation]

        self._container_layout = layout_cls(self._widget)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(2)

        self._layout = layout_cls()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._container_layout.addLayout(self._layout)

        self._container_layout.addStretch(1)

        self._dragged_widget: QWidget | None = None
        self._dragged = False

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidget(self._widget)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self._widgets_moved.connect(
            self._on_widgets_moved, Qt.ConnectionType.QueuedConnection
        )

    def child_widget(self) -> QWidget:
        return self._widget

    def _find_widget_at(self, point: QPoint) -> tuple[int, QWidget] | None:
        """
        Find the child widget of _widget that intersects with the given point.
        point is relative to _widget.
        """
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item is None:
                continue
            child = item.widget()
            if child is None:
                continue
            if child.geometry().contains(point):
                return i, child
        return None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent) and isinstance(obj, QWidget):
            if self._dragged_widget is None:
                if (
                    event.type() == QEvent.Type.MouseButtonPress
                    and self._layout.indexOf(obj) != -1
                ):
                    self._dragged_widget = obj
                    self._dragged = False
            elif self._dragged_widget is obj:
                if event.type() == QEvent.Type.MouseButtonRelease:
                    self._dragged_widget = None
                    dragged = self._dragged
                    self._dragged = False
                    if dragged:
                        return True
                elif event.type() == QEvent.Type.MouseMove:
                    self._move_dragged_to_cursor()
        elif obj is self._widget and isinstance(event, QResizeEvent):
            self.resized.emit()
        return super().eventFilter(obj, event)

    def _move_dragged_to_cursor(self) -> None:
        assert self._dragged_widget is not None
        found = self._find_widget_at(self._widget.mapFromGlobal(QCursor.pos()))
        if found is not None:
            i, child = found
            if self._dragged_widget is not child:
                self._layout.removeWidget(self._dragged_widget)
                self._layout.insertWidget(i, self._dragged_widget)
                self._widgets_moved.emit()
                self._dragged = True

    def add_item(self, item: QWidget) -> None:
        self._layout.addWidget(item)
        item.installEventFilter(self)

    def sizeHint(self) -> QSize:
        return self._size_hint

    def minimumSizeHint(self) -> QSize:
        return self._size_hint

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.resized.emit()

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Enter and leave events are not generated automatically when scrolling.
        # This manually generates them.

        # Store which widget the mouse is over
        global_pos = QCursor.pos()
        old_pos = self._widget.mapFromGlobal(global_pos)
        old_state = self._find_widget_at(old_pos)
        old_widget = None if old_state is None else old_state[1]

        bar = (
            self.horizontalScrollBar()
            if self._orientation == Qt.Orientation.Horizontal
            else self.verticalScrollBar()
        )
        bar.setValue(bar.value() - event.angleDelta().y() // 5)

        self._widgets_moved.emit()
        if self._dragged_widget is not None:
            self._move_dragged_to_cursor()
            return

        # Get the new widget the mouse is over
        new_pos = self._widget.mapFromGlobal(global_pos)
        new_state = self._find_widget_at(new_pos)
        new_widget = None if new_state is None else new_state[1]
        # If the mouse is over a different widget manually generate the leave and enter events.
        # Qt does not generate them automatically for some reason.
        if old_widget != new_widget:
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

    def scroll_up(self) -> None:
        if self._orientation == Qt.Orientation.Vertical:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 60)
        else:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 60)
        self._widgets_moved.emit()

    def scroll_down(self) -> None:
        if self._orientation == Qt.Orientation.Vertical:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 60)
        else:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 60)
        self._widgets_moved.emit()

    def show_labels(self) -> None:
        visible_rect = QRect(-self._widget.pos(), self.viewport().size())
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, ToolbarButton) and visible_rect.contains(
                widget.geometry()
            ):
                widget.show_tooltip()

    def hide_labels(self) -> None:
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, ToolbarButton):
                widget.hide_tooltip()

    def _on_widgets_moved(self) -> None:
        visible_rect = QRect(-self._widget.pos(), self.viewport().size())
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, ToolbarButton):
                widget.hide_tooltip()
                if visible_rect.contains(widget.geometry()):
                    widget.show_tooltip()


class ToolBar(QWidget):
    """
    A toolbar is a strip of buttons.
    The first half can be rearranged and the second half are fixed.
    """

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
    ) -> None:
        super().__init__()
        self._orientation = orientation
        layout_cls = LayoutCls[orientation]

        self._main_layout = layout_cls(self)
        self._main_layout.setSpacing(2)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        self._dynamic_button_widget = DynamicButtonWidget(self, orientation)
        self._main_layout.addWidget(self._dynamic_button_widget, 1)

        self._arrow_widget = QWidget()
        self._main_layout.addWidget(self._arrow_widget)

        if orientation == Qt.Orientation.Vertical:
            direction = QBoxLayout.Direction.LeftToRight
            up_label = "˄"
            down_label = "˅"
        else:
            direction = QBoxLayout.Direction.TopToBottom
            up_label = "˂"
            down_label = "˃"

        self._arrow_layout = QBoxLayout(direction, self._arrow_widget)
        self._arrow_layout.setContentsMargins(0, 0, 0, 0)
        self._arrow_layout.setSpacing(0)

        self._up_arrow = QPushButton(up_label)
        self._up_arrow.setFixedSize(ButtonSize // 2, ButtonSize // 2)
        self._up_arrow.clicked.connect(self._dynamic_button_widget.scroll_up)
        self._arrow_layout.addWidget(self._up_arrow)

        self._down_arrow = QPushButton(down_label)
        self._down_arrow.setFixedSize(ButtonSize // 2, ButtonSize // 2)
        self._down_arrow.clicked.connect(self._dynamic_button_widget.scroll_down)
        self._arrow_layout.addWidget(self._down_arrow)

        size_policy = self._arrow_widget.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        self._arrow_widget.setSizePolicy(size_policy)
        self._dynamic_button_widget.resized.connect(self._on_dynamic_resize)

        self._static_button_layout = layout_cls()
        self._main_layout.addLayout(self._static_button_layout)

        self._button_group = QButtonGroup()

    def _on_dynamic_resize(self) -> None:
        widget = self._button_group.checkedButton()
        if widget is not None and self._dynamic_button_widget.isAncestorOf(widget):
            self._dynamic_button_widget.ensureWidgetVisible(widget, 0, 0)
        if self._orientation == Qt.Orientation.Vertical:
            self._arrow_widget.setVisible(
                self._dynamic_button_widget.height()
                < self._dynamic_button_widget.child_widget().sizeHint().height()
            )
        else:
            self._arrow_widget.setVisible(
                self._dynamic_button_widget.width()
                < self._dynamic_button_widget.child_widget().sizeHint().width()
            )

    def add_layout_button(self) -> ToolbarButton:
        """Add a button to the toolbar."""
        button = ToolbarButton()
        button.setFixedSize(QSize(ButtonSize, ButtonSize))
        button.setIconSize(QSize(IconSize, IconSize))
        button.setCheckable(True)
        self._button_group.addButton(button)
        self._dynamic_button_widget.add_item(button)
        return button

    def uncheck_layout_buttons(self) -> None:
        button = self._button_group.checkedButton()
        if button is not None:
            button.setChecked(False)

    def add_static_button(self) -> ToolbarButton:
        """Add a button to the toolbar."""
        button = ToolbarButton()
        button.setFixedSize(QSize(ButtonSize, ButtonSize))
        button.setIconSize(QSize(IconSize, IconSize))
        self._static_button_layout.insertWidget(0, button)
        return button

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)

        self._dynamic_button_widget.show_labels()

        for i in range(self._static_button_layout.count()):
            item = self._static_button_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, ToolbarButton):
                widget.show_tooltip()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)

        self._dynamic_button_widget.hide_labels()

        for i in range(self._static_button_layout.count()):
            item = self._static_button_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, ToolbarButton):
                widget.hide_tooltip()
