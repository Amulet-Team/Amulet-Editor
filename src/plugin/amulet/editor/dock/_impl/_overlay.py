"""
These widgets provide an overlay to show the user where something is going to be dropped.
"""

from __future__ import annotations

from enum import IntEnum
from weakref import ref

from PySide6.QtCore import QPoint, QSize, Qt, QRect
from PySide6.QtGui import (
    QPaintEvent,
    QPainter,
    QColor,
    QResizeEvent,
    QPolygon,
    QCursor,
)
from PySide6.QtWidgets import QWidget

from . import _tab_widget


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
