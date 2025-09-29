"""Classes to facilitate dragging tabs."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from enum import IntEnum

from PySide6.QtCore import QObject, QEvent, QPoint, QSize, Qt
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

from plugin.amulet.editor.widget.abc import TabWidget


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

        normal_colour = QColor(115, 215, 255, 128)
        painter.setBrush(normal_colour)
        painter.drawRect(self.rect())
        painter.end()


class TabContainerOverlay(QWidget):
    """A class to implement tab bar highlighting."""

    def __init__(self, parent: TabContainerWidget) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.move(0, 0)
        self.resize(parent.size())
        self.show()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        normal_colour = QColor(115, 215, 255, 128)
        painter.setBrush(normal_colour)
        painter.drawRect(self.rect())
        painter.end()


class SplitterDropOverlay(QWidget):
    """A class to implement 5-way splitter drop highlighting."""

    class DropArea(IntEnum):
        Top = 0
        Right = 1
        Bottom = 2
        Left = 3
        Middle = 4

    def __init__(self, target: QWidget) -> None:
        super().__init__(target)
        self.target = target
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.shape = QSize(-1, -1)
        self.polygons: list[QPolygon] = []
        self.drop_area: SplitterDropOverlay.DropArea | None = None

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

        for drop, poly in zip(self.DropArea, self.polygons):
            if self.drop_area is None and poly.containsPoint(
                cursor_point, Qt.FillRule.OddEvenFill
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
        self, widget: TabContainerWidget, overlay: TabContainerOverlay
    ) -> None:
        self.hover_widget = widget
        self.overlay = overlay


class SplitterHoverState:
    def __init__(self, widget: TabWidgetStack, overlay: SplitterDropOverlay) -> None:
        self.hover_widget = widget
        self.overlay = overlay


class ExternalHoverState:
    def __init__(self, overlay: CuboidDropOverlay) -> None:
        self.overlay = overlay


class TabDragManager(QObject):
    """A class to manage the dragging of a tab."""

    def __init__(self, tab_widget: TabWidget) -> None:
        super().__init__()
        self._tab_widget = tab_widget
        self._tab = tab_widget.tab

        self._drag_start_point: QPoint | None = None
        self._dragging = False

        self._hover_state: (
            TabBarHoverState | SplitterHoverState | ExternalHoverState | None
        ) = None

    def __del__(self) -> None:
        print("TabDragManager.__del__()")

    def _drag_start(self, event: QMouseEvent) -> None:
        print("Drag start")

        # Remove button and widget
        stack = get_tab_widget_stack(self._tab)
        stack._steal_tab_widget(self._tab_widget)

        # Set tab styling
        self._tab.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._tab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._tab.setEnabled(False)

        # Show and capture mouse
        self._tab.show()
        self._tab.grabMouse()

    def _get_drop_widget_at(
        self, point: QPoint
    ) -> TabWidgetStack | TabContainerWidget | None:
        widget: QObject | None = QApplication.widgetAt(point)
        while widget is not None:
            if isinstance(widget, (TabWidgetStack, TabContainerWidget)):
                return widget
            widget = widget.parent()
        return None

    def _drag(self, event: QMouseEvent) -> None:
        # Get the mouse position
        point = event.globalPosition().toPoint()

        # Move the tap to the new mouse location
        self._tab.move(point)

        # Find the widget under the mouse
        widget = self._get_drop_widget_at(point)

        # Update highlighting
        if isinstance(self._hover_state, ExternalHoverState):
            if widget is None:
                self._hover_state.overlay.move(point)
            else:
                self._hover_state.overlay.close()
                self._hover_state = None
        elif isinstance(self._hover_state, (TabBarHoverState, SplitterHoverState)):
            if self._hover_state.hover_widget is widget:
                # Update existing overlay
                self._hover_state.overlay.update()
            else:
                # Not hovering over this widget anymore
                self._hover_state.overlay.close()
                self._hover_state = None

        if self._hover_state is None:
            if widget is None:
                self._hover_state = ExternalHoverState(
                    CuboidDropOverlay(point, QSize(400, 400))
                )
                self._tab.raise_()
            elif isinstance(widget, TabContainerWidget):
                self._hover_state = TabBarHoverState(
                    widget, TabContainerOverlay(widget)
                )
            elif isinstance(widget, TabWidgetStack):
                self._hover_state = SplitterHoverState(
                    widget, SplitterDropOverlay(widget)
                )

    def _drag_stop(self, event: QMouseEvent) -> None:
        print("Drop")

        # disconnect from button events
        self._tab.releaseMouse()
        self._tab.removeEventFilter(self)
        set_tab_data(self._tab_widget, None)

        # Reset button styling
        self._tab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._tab.setEnabled(True)

        hover_state = self._hover_state

        if isinstance(hover_state, TabBarHoverState):
            hover_state.overlay.close()
            stack_widget = get_tab_widget_stack(hover_state.hover_widget)
            stack_widget._add_tab_widget(self._tab_widget)
        elif isinstance(hover_state, SplitterHoverState):
            hover_state.overlay.close()
            drop_area = hover_state.overlay.drop_area
            if drop_area == SplitterDropOverlay.DropArea.Middle:
                hover_state.hover_widget._add_tab_widget(self._tab_widget)
            # TODO: split the splitter
            pass
        elif isinstance(hover_state, ExternalHoverState):
            hover_state.overlay.close()
            # TODO: create a new sub-window

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


from ._tab_widget import (
    TabWidgetStack,
    TabContainerWidget,
    get_tab_widget_stack,
    set_tab_data,
)
