"""Classes to facilitate dragging tabs."""

from __future__ import annotations

from enum import IntEnum
from weakref import ref
import logging

from PySide6.QtCore import QObject, QEvent, QPoint, QSize, Qt, QRect
from PySide6.QtGui import (
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QColor,
    QResizeEvent,
    QPolygon,
    QCursor,
)
from PySide6.QtWidgets import QWidget, QApplication

from . import _tab_widget
from . import _child_window

log = logging.getLogger(__name__)


class CuboidDropOverlay(QWidget):
    """A class to implement cuboid highlighting."""

    def __init__(self, origin: QPoint, size: QSize) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.move(origin)
        self.resize(size)
        self.show()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(QColor(115, 215, 255, 128))
        painter.setPen(QColor(115, 215, 255))
        painter.drawRect(self.rect())
        painter.end()


class TabContainerOverlay(QWidget):
    """A class to implement tab bar highlighting."""

    def __init__(self, parent: _tab_widget.TabContainerWidget) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.move(0, 0)
        self.resize(parent.size())
        self.show()

        self.index: int | None = None

    def paintEvent(self, event: QPaintEvent) -> None:
        parent = self.parent()
        if not isinstance(parent, _tab_widget.TabContainerWidget):
            return

        def tab_x_pos(tab_: _tab_widget.TabButton) -> int:
            return tab_.x()

        tabs = sorted(parent.findChildren(_tab_widget.TabButton), key=tab_x_pos)

        cursor_point = QCursor.pos() - parent.mapToGlobal(QPoint(0, 0))
        cursor_x = cursor_point.x()

        for i in range(len(tabs)):
            tab = tabs[i]
            if tab.x() <= cursor_x < tab.x() + tab.width():
                # Cursor intersects this tab
                if cursor_x < tab.x() + tab.width() // 2:
                    # left
                    x = tab.x()
                    y = tab.y()
                    width = tab.width() // 2
                    height = tab.height()
                    if 0 < i:
                        left_tab = tabs[i - 1]
                        x -= left_tab.width() - left_tab.width() // 2
                        width += left_tab.width() // 2
                    rect = QRect(x, y, width, height)
                    self.index = i
                else:
                    # right
                    x = tab.x() + tab.width() // 2
                    y = tab.y()
                    width = tab.width() // 2
                    height = tab.height()
                    if i < len(tabs) - 1:
                        right_tab = tabs[i + 1]
                        width += right_tab.width() // 2
                    else:
                        width = parent.width() - x
                    rect = QRect(x, y, width, height)
                    self.index = i + 1
                break
        else:
            if tabs:
                tab = tabs[-1]
                x = tab.x() + tab.width() // 2
                y = tab.y()
                width = parent.width() - x
                height = tab.height()
                rect = QRect(x, y, width, height)
            else:
                rect = parent.rect()
            self.index = None

        painter = QPainter(self)
        painter.setBrush(QColor(115, 215, 255, 128))
        painter.setPen(QColor(115, 215, 255))
        painter.drawRect(rect)
        painter.end()


class DropArea(IntEnum):
    Top = 0
    Right = 1
    Bottom = 2
    Left = 3
    Middle = 4


class SplitterDropOverlay(QWidget):
    """A class to implement 5-way splitter drop highlighting."""

    def __init__(self, target: _tab_widget.WidgetStack) -> None:
        super().__init__(target)
        self._target_ref = ref(target)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.shape = QSize(-1, -1)
        self.polygons: list[QPolygon] = []
        self.drop_area: DropArea | None = None

        self.move(0, 0)
        self.resize(target.size())
        self._compute_polygons()
        self.show()

    def _compute_polygons(self) -> None:
        shape = self.size()
        if shape != self.shape:
            width = self.width()
            height = self.height()
            inset_amount = 3.5
            inset_width = int(width / inset_amount)
            inset_height = int(height / inset_amount)

            top_left = QPoint(0, 0)
            top_right = QPoint(width, 0)
            bottom_right = QPoint(width, height)
            bottom_left = QPoint(0, height)

            middle_top_left = QPoint(inset_width, inset_height)
            middle_top_right = QPoint(width - inset_width, inset_height)
            middle_bottom_right = QPoint(width - inset_width, height - inset_height)
            middle_bottom_left = QPoint(inset_width, height - inset_height)

            self.polygons = [
                QPolygon([top_left, top_right, middle_top_right, middle_top_left]),
                QPolygon(
                    [top_right, bottom_right, middle_bottom_right, middle_top_right]
                ),
                QPolygon(
                    [bottom_right, bottom_left, middle_bottom_left, middle_bottom_right]
                ),
                QPolygon([bottom_left, top_left, middle_top_left, middle_bottom_left]),
                QPolygon(
                    [
                        middle_top_left,
                        middle_top_right,
                        middle_bottom_right,
                        middle_bottom_left,
                    ]
                ),
            ]

            self.shape = shape

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._compute_polygons()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        cursor_point = QCursor.pos() - self.mapToGlobal(QPoint(0, 0))

        normal_colour = QColor(115, 215, 255, 128)
        painter.setBrush(normal_colour)
        painter.setPen(QColor(115, 215, 255))

        self.drop_area = None

        target = self._target_ref()
        if target is not None and len(target.children()) <= 3:
            # only has the layout, new tab page and this class as children. Don't split it.
            painter.drawRect(target.rect())
        else:
            for drop, poly in zip(DropArea, self.polygons):
                if self.drop_area is None and (
                    poly.containsPoint(cursor_point, Qt.FillRule.OddEvenFill)
                    or drop is DropArea.Middle
                ):
                    painter.setBrush(QColor(115, 215, 255, 190))
                    painter.drawPolygon(poly)
                    painter.setBrush(normal_colour)
                    self.drop_area = drop
                else:
                    painter.drawPolygon(poly)
                painter.drawPolyline(poly)

        painter.end()


class TabBarHoverState:
    def __init__(
        self, widget: _tab_widget.TabContainerWidget, overlay: TabContainerOverlay
    ) -> None:
        self.hover_widget = widget
        self.overlay = overlay


class SplitterHoverState:
    def __init__(
        self, widget: _tab_widget.WidgetStack, overlay: SplitterDropOverlay
    ) -> None:
        self.hover_widget = widget
        self.overlay = overlay


class ExternalHoverState:
    def __init__(self, overlay: CuboidDropOverlay) -> None:
        self.overlay = overlay


ActiveTabDragManager: TabDragManager | None = None


class TabDragManager(QObject):
    """A class to manage the dragging of a tab."""

    def __init__(
        self,
        stack_widget: _tab_widget.TabWidgetStack,
        tab_widget_meta: _tab_widget.TabWidgetMeta,
    ) -> None:
        super().__init__()
        self._tab_widget_meta = tab_widget_meta
        self._tab = tab_widget_meta.tab

        self._stack_widget_ref = ref[_tab_widget.TabWidgetStack](stack_widget)

        self._drag_start_point: QPoint | None = None
        self._dragging = False

        self._hover_state: (
            TabBarHoverState | SplitterHoverState | ExternalHoverState | None
        ) = None

    def __del__(self) -> None:
        log.debug(f"TabDragManager.__del__()")

    def _drag_start(self, event: QMouseEvent) -> None:
        log.debug(f"TabDragManager._drag_start({self})")

        global ActiveTabDragManager
        ActiveTabDragManager = self

        # Remove button and widget
        stack = self._stack_widget_ref()
        if stack is None:
            raise RuntimeError("TabWidgetStack has been destroyed")
        stack._steal_tab_widget(self._tab_widget_meta)

        # Set tab styling
        self._tab.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._tab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._tab.setEnabled(False)

        # Show and capture mouse
        self._tab.show()
        self._tab.grabMouse()

    @staticmethod
    def _get_drop_widget_at(
        point: QPoint,
    ) -> _tab_widget.WidgetStack | _tab_widget.TabContainerWidget | None:
        widget: QObject | None = QApplication.widgetAt(point)
        while widget is not None:
            if isinstance(
                widget, (_tab_widget.WidgetStack, _tab_widget.TabContainerWidget)
            ):
                return widget
            widget = widget.parent()
        return None

    def _drag(self, event: QMouseEvent) -> None:
        # Get the mouse position
        point = event.globalPosition().toPoint()

        # Move the tap to the new mouse location
        # self._tab.move(point + QPoint(-(self._tab.width() // 2), -(self._tab.height() // 2)))
        self._tab.move(point + QPoint(1, 1))
        # Find the widget under the mouse
        widget = self._get_drop_widget_at(point)

        # Update highlighting
        if isinstance(self._hover_state, ExternalHoverState):
            if widget is None:
                self._hover_state.overlay.move(point + QPoint(1, 1))
            else:
                self._hover_state.overlay.deleteLater()
                self._hover_state = None
        elif isinstance(self._hover_state, (TabBarHoverState, SplitterHoverState)):
            if self._hover_state.hover_widget is widget:
                # Update existing overlay
                self._hover_state.overlay.update()
            else:
                # Not hovering over this widget anymore
                self._hover_state.overlay.deleteLater()
                self._hover_state = None

        if self._hover_state is None:
            if widget is None:
                self._hover_state = ExternalHoverState(
                    CuboidDropOverlay(point + QPoint(1, 1), QSize(400, 400))
                )
                self._tab.raise_()
            elif isinstance(widget, _tab_widget.TabContainerWidget):
                self._hover_state = TabBarHoverState(
                    widget, TabContainerOverlay(widget)
                )
            elif isinstance(widget, _tab_widget.WidgetStack):
                self._hover_state = SplitterHoverState(
                    widget, SplitterDropOverlay(widget)
                )

    def _drag_stop(self, event: QMouseEvent) -> None:
        log.debug(f"TabDragManager._drag_stop({self})")
        global ActiveTabDragManager

        # disconnect from button events
        self._tab.releaseMouse()

        def on_destroy() -> None:
            log.debug("Tab is being destroyed")

        self._tab.destroyed.connect(on_destroy)

        # Reset button styling
        self._tab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._tab.setEnabled(True)

        hover_state = self._hover_state
        old_stack_widget = self._stack_widget_ref()
        if old_stack_widget is None:
            raise RuntimeError("TabWidgetStack has been destroyed")

        if isinstance(hover_state, TabBarHoverState):
            hover_state.overlay.deleteLater()
            stack_widget = _tab_widget.get_tab_widget_stack(hover_state.hover_widget)
            old_stack_widget._disconnect_tab_widget(
                self._tab_widget_meta, old_stack_widget is not stack_widget
            )
            index = hover_state.overlay.index
            if index is None:
                index = -1
            stack_widget._insert_tab_widget(index, self._tab_widget_meta)
        elif isinstance(hover_state, SplitterHoverState):
            hover_state.overlay.deleteLater()
            drop_area = hover_state.overlay.drop_area
            stack_widget = _tab_widget.get_tab_widget_stack(hover_state.hover_widget)
            old_stack_widget._disconnect_tab_widget(
                self._tab_widget_meta, old_stack_widget is not stack_widget
            )
            if (
                drop_area is None
                or drop_area == DropArea.Middle
                or stack_widget._is_empty()
            ):
                stack_widget._add_tab_widget(self._tab_widget_meta)
            else:
                new_stack_widget = _tab_widget.TabWidgetStack()
                new_stack_widget._add_tab_widget(self._tab_widget_meta)
                stack_widget.split.emit(stack_widget, new_stack_widget, drop_area)
        elif isinstance(hover_state, ExternalHoverState):
            hover_state.overlay.deleteLater()
            old_stack_widget._disconnect_tab_widget(self._tab_widget_meta)
            tab_widget = _tab_widget.TabWidgetStack()
            tab_widget._add_tab_widget(self._tab_widget_meta)
            new_window = _child_window.create_sub_window(tab_widget)
            new_window.resize(400, 400)
            new_window.move(event.globalPosition().toPoint())
            new_window.show()

        log.debug("Activate new tab widget")
        self._tab.click()
        ActiveTabDragManager = None

    def _mouse_event(self, event: QMouseEvent) -> None:
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_point = event.pos()
        elif event.type() == QEvent.Type.MouseMove:
            if self._dragging:
                self._drag(event)
            elif (
                self._drag_start_point is not None
                and 5 < (self._drag_start_point - event.pos()).manhattanLength()
            ):
                self._dragging = True
                self._drag_start(event)
                self._drag(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._dragging:
                    self._dragging = False
                    self._drag_stop(event)
                self._drag_start_point = None

    def eventFilter(self, watched: QObject, event: QEvent, /) -> bool:
        if watched is self._tab:
            if isinstance(event, QMouseEvent):
                self._mouse_event(event)
        return False
