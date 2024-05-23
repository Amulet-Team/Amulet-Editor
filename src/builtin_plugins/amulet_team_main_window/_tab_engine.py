"""
This is a generic tab engine system.
You must subclass the abstract classes and implement custom handling for the following cases.
1) When the last tab is removed
2) When a tab is dropped into empty space
"""

from __future__ import annotations
from typing import Optional, Union, overload, Any
from enum import IntEnum

from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QLabel,
    QSplitter,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QMouseEvent,
    QResizeEvent,
    QWheelEvent,
    QColor,
    QPaintEvent,
    QPolygon,
    QCursor,
)
from PySide6.QtCore import (
    Signal,
    Slot,
    QPoint,
    Qt,
    QObject,
    QSize,
)

from amulet_editor.models.widgets.traceback_dialog import DisplayException
import tablericons


_button_size: Optional[QSize] = None


def button_size() -> QSize:
    global _button_size
    if _button_size is None:
        _button_size = QPushButton().sizeHint()
    return _button_size


class TabWidget(QWidget):
    @property
    def name(self) -> str:
        # TODO: convert this to a translation key
        return "TabWidgetNameGoesHere"

    @property
    def icon(self) -> Optional[QIcon]:
        return None

    def disable_view(self) -> None:
        """
        This is run when a view is about to be removed from a view container.
        This gives the view a chance to do any cleaning up before it is removed and potentially destroyed.
        This method must leave the view in a state where it can be destroyed or activated again.
        """
        pass


class TabButton(QFrame):
    """A tab button."""

    def __init__(self, label: str, icon: Optional[QIcon]):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.layout_ = QHBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout_)
        self.layout_.addStretch()
        self.layout_.addWidget(QLabel(label))
        self.layout_.addStretch()
        self.close_button = QPushButton()
        size = int(button_size().height() * 0.75)
        self.close_button.setFixedSize(size, size)
        self.close_button.setIcon(QIcon(tablericons.x))
        self.close_button.setFlat(True)
        self.layout_.addWidget(self.close_button)

    def display_clicked(self) -> None:
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)

    def display_unclicked(self) -> None:
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)

    def sizeHint(self) -> QSize:
        return QSize(-1, button_size().height())


class DropArea(IntEnum):
    Top = 0
    Right = 1
    Bottom = 2
    Left = 3
    Middle = 4


class DragSplitRenderer(QWidget):
    """A class to implement custom drawing while the user is dragging a tab."""

    def __init__(self, target: QWidget) -> None:
        super().__init__(target)
        self.target = target
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.shape = QSize(-1, -1)
        self.polygons: list[QPolygon] = []
        self.drop_area: Optional[DropArea] = None

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

        for drop, poly in zip(DropArea, self.polygons):
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


class DragTabRenderer(QWidget):
    """A class to implement custom drawing while the user is dragging a tab."""

    def __init__(self, target: QWidget) -> None:
        super().__init__(target)
        self.target = target
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.drop_index = 0

        self.move(0, 0)
        self.resize(target.size())
        self.show()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        normal_colour = QColor(115, 215, 255, 128)
        painter.setBrush(normal_colour)
        painter.drawRect(self.rect())
        painter.end()


class AbstractTabContainerWidget(QWidget):
    """
    A widget containing tab buttons.
    This represents the whole area including the area off screen.
    """

    tab_changed = Signal(int)

    drag_start_pos: QPoint
    active_button: Optional[TabButton]

    # The widget being dragged or None
    dragged_widget: TabWidget | None
    # The widget that was previously highlighted
    highlight_widget: Union[
        None,
        tuple[AbstractStackedTabWidget, DragSplitRenderer],
        tuple[AbstractTabContainerWidget, DragTabRenderer],
    ]

    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, f)
        self.setAcceptDrops(True)
        self.drag_start_pos = QPoint()
        self.layout_ = QHBoxLayout(self)
        self.layout_.setSpacing(0)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.active_button = None
        self.dragged_widget = None
        self.highlight_widget = None

    def add_tab(self, label: str, icon: QIcon | None = None)  -> None:
        tab = TabButton(label, icon)
        if self.active_button is None:
            self.active_button = tab
            tab.display_clicked()
        else:
            tab.display_unclicked()
        self.layout_.addWidget(tab)

    def insert_tab(self, index: int, label: str, icon: QIcon | None = None) -> None:
        tab = TabButton(label, icon)
        if self.active_button is None:
            self.active_button = tab
            tab.display_clicked()
        else:
            tab.display_unclicked()
        self.layout_.insertWidget(index, tab)

    def remove_tab(self, index: int) -> None:
        item = self.layout_.itemAt(index)
        widget = item.widget()
        self.layout_.removeItem(item)
        is_active = widget == self.active_button
        widget.hide()
        widget.deleteLater()
        if is_active:
            if self.count():
                active_index = min(self.count() - 1, index)
                item = self.layout_.itemAt(active_index)
                button_widget = item.widget()
                assert isinstance(button_widget, TabButton)
                self.active_button = button_widget
                self.active_button.display_clicked()
            else:
                self.active_button = None

    def count(self) -> int:
        return self.layout_.count()

    def current_index(self) -> int:
        if self.active_button is not None:
            return self.layout_.indexOf(self.active_button)
        return -1

    @property
    def container(self) -> AbstractTabContainer:
        parent = self.parent().parent()
        if not isinstance(parent, AbstractTabContainer):
            raise RuntimeError(
                "Parent of AbstractTabContainerWidget must be AbstractTabContainer"
            )
        return parent

    def _get_button_at(self, point: QPoint) -> TabButton | None:
        child: QObject = self.childAt(point)
        if child is None:
            return
        while child.parent() != self:
            child = child.parent()
        if isinstance(child, TabButton):
            return child
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # If left-clicked
        if event.button() == Qt.MouseButton.LeftButton:
            # Store the click position
            self.drag_start_pos = event.position().toPoint()
            # Get the tab button that was clicked (if any)
            button = self._get_button_at(self.drag_start_pos)
            if button is None:
                return
            # Deactivate the previously clicked button
            old_button = self.active_button
            if old_button is not None:
                old_button.display_unclicked()
            # Active the clicked button
            button.display_clicked()
            self.active_button = button
            # Notify of tab change
            self.tab_changed.emit(self.layout_.indexOf(button))
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # If the mouse has been clicked and dragged beyond the minimum distance then start dragging
        if self.dragged_widget is not None:
            # Drag has already started. Update the widget display.
            widget = self._get_drop_widget(event.globalPosition().toPoint())
            if self.highlight_widget is not None:
                old_widget, render_widget = self.highlight_widget
                if old_widget is widget:
                    # Draw hook already installed. Just update it
                    render_widget.update()
                else:
                    # Not hovering over this widget anymore
                    render_widget.close()
                    self.highlight_widget = None

            if self.highlight_widget is None:
                if isinstance(widget, AbstractStackedTabWidget):
                    render_widget = DragSplitRenderer(widget)
                    self.highlight_widget = widget, render_widget
                elif isinstance(widget, AbstractTabContainerWidget):
                    render_widget = DragTabRenderer(widget)
                    self.highlight_widget = widget, render_widget

        elif (
            event.buttons() & Qt.MouseButton.LeftButton
            and self.active_button is not None
            and not self.drag_start_pos.isNull()
            and (
                (event.position() - self.drag_start_pos).manhattanLength()
                >= QApplication.startDragDistance()
            )
        ):
            # The user has clicked and dragged beyond the minimum distance
            # Get the tab display
            pixmap = self.active_button.grab()
            target_pixmap = QPixmap(pixmap.size())
            target_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(target_pixmap)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            # Remove the tab
            tab_index = self.layout_.indexOf(self.active_button)
            self.dragged_widget = self.container.tab_bar.tab_widget.remove_page(
                tab_index
            )
            # Start drag. This widget will get all mouse events.
            self.grabMouse(target_pixmap)
        else:
            super().mouseMoveEvent(event)

    def _get_drop_widget(
        self, point: QPoint
    ) -> Union[None, AbstractTabContainerWidget, AbstractStackedTabWidget]:
        """Get the widget that the dragged widget will be dropped into."""
        widget: QObject = QApplication.widgetAt(point)
        while widget is not None:
            if isinstance(
                widget, (AbstractTabContainerWidget, AbstractStackedTabWidget)
            ):
                return widget
            widget = widget.parent()
        return None

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.dragged_widget is None:
            # If not dragging. Reset values
            self.drag_start_pos = QPoint()
        elif not event.buttons() & Qt.MouseButton.LeftButton:
            # If dragging and left mouse has been released. Drop the widget
            # Find where the drop happened and update the widget
            self.releaseMouse()

            widget, render_widget = self.highlight_widget or (None, None)
            if isinstance(widget, AbstractTabContainerWidget) and isinstance(
                render_widget, DragTabRenderer
            ):
                # Dropped into a tab bar
                widget.container.tab_bar.tab_widget.add_page(self.dragged_widget)
            elif isinstance(widget, AbstractStackedTabWidget) and isinstance(
                render_widget, DragSplitRenderer
            ):
                drop_area = render_widget.drop_area
                if drop_area is DropArea.Middle:
                    widget.add_page(self.dragged_widget)
                else:
                    # Dropped onto a stacked tab widget. Replace the widget with a splitter
                    splitter = widget.splitter
                    splitter_index = splitter.indexOf(widget)
                    sizes = splitter.sizes()

                    widget.setParent(None)

                    new_splitter = RecursiveSplitter()

                    new_splitter.addWidget(widget)

                    tab_widget = self._new_stacked_tab_widget()
                    tab_widget.add_page(self.dragged_widget)
                    if drop_area in {DropArea.Top, DropArea.Bottom}:
                        new_splitter.setOrientation(Qt.Orientation.Vertical)
                    else:
                        new_splitter.setOrientation(Qt.Orientation.Horizontal)
                    if drop_area in {DropArea.Top, DropArea.Left}:
                        new_splitter.insertWidget(0, tab_widget)
                    else:
                        new_splitter.addWidget(tab_widget)

                    splitter.insertWidget(splitter_index, new_splitter)
                    splitter.setSizes(sizes)
                    new_splitter.setSizes([2048, 2048])
            else:
                # Dropped into space or a non-compatible widget
                self._on_drop_in_space(self.dragged_widget, event)

            if render_widget is not None:
                render_widget.close()

            self.container.tab_bar.tab_widget.clean_up()
            self.drag_start_pos = QPoint()
            self.dragged_widget = None
            self.highlight_widget = None
        else:
            super().mouseReleaseEvent(event)

    def _new_stacked_tab_widget(self) -> AbstractStackedTabWidget:
        raise NotImplementedError

    def _on_drop_in_space(
        self, dragged_widget: TabWidget, drop_event: QMouseEvent
    ) -> None:
        raise NotImplementedError


class AbstractTabContainer(QScrollArea):
    """A scrollable widget to contain tab buttons."""

    tab_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tab_container_widget = self._new_tab_container_widget()
        self.tab_container_widget.tab_changed.connect(self.tab_changed)
        self.setWidget(self.tab_container_widget)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.verticalScrollBar().hide()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.horizontalScrollBar().hide()

    def _new_tab_container_widget(self) -> AbstractTabContainerWidget:
        raise NotImplementedError

    @property
    def tab_bar(self) -> AbstractTabBar:
        parent = self.parent()
        if not isinstance(parent, AbstractTabBar):
            raise RuntimeError("Parent of AbstractTabContainer must be AbstractTabBar")
        return parent

    def sizeHint(self) -> QSize:
        return self.tab_container_widget.layout_.sizeHint()

    def wheelEvent(self, event: QWheelEvent) -> None:
        scroll_bar = self.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() - event.angleDelta().y())


class AbstractTabBar(QWidget):
    """A custom class that behaves like a QTabBar."""

    tab_changed = Signal(int)
    add_clicked = Signal()

    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, f)
        self.layout_ = QHBoxLayout(self)
        self.layout_.setSpacing(0)
        self.layout_.setContentsMargins(0, 0, 0, 0)

        button_height = button_size().height()

        self.left_button = QPushButton("<")
        self.left_button.setFixedSize(button_height, button_height)
        self.layout_.addWidget(self.left_button)
        self.left_button.clicked.connect(self._move_left)

        self.tab_container = self._new_tab_container()
        self.tab_container.tab_changed.connect(self.tab_changed)
        self.layout_.addWidget(self.tab_container)

        self.right_button = QPushButton(">")
        self.right_button.setFixedSize(button_height, button_height)
        self.layout_.addWidget(self.right_button)
        self.right_button.clicked.connect(self._move_right)

        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(button_height, button_height)
        self.layout_.addWidget(self.plus_button)
        self.plus_button.clicked.connect(self.add_clicked)

    def _new_tab_container(self) -> AbstractTabContainer:
        raise NotImplementedError

    def add_tab(self, label: str, icon: QIcon | None = None) -> None:
        self.tab_container.tab_container_widget.add_tab(label, icon)
        self._check_size()

    def insert_tab(self, index: int, label: str, icon: QIcon | None = None) -> None:
        self.tab_container.tab_container_widget.insert_tab(index, label, icon)
        self._check_size()

    def remove_tab(self, index: int) -> None:
        self.tab_container.tab_container_widget.remove_tab(index)
        self._check_size()

    def count(self) -> int:
        return self.tab_container.tab_container_widget.count()

    def current_index(self) -> int:
        return self.tab_container.tab_container_widget.current_index()

    @property
    def tab_widget(self) -> AbstractStackedTabWidget:
        parent = self.parent()
        if not isinstance(parent, AbstractStackedTabWidget):
            raise RuntimeError(
                "Parent of AbstractTabBar must be AbstractStackedTabWidget"
            )
        return parent

    def _check_size(self) -> None:
        if (
            self.tab_container.size().width()
            + self.left_button.width() * self.left_button.isVisible()
            + self.right_button.width() * self.right_button.isVisible()
            > self.tab_container.sizeHint().width()
        ):
            self.left_button.hide()
            self.right_button.hide()
        else:
            self.left_button.show()
            self.right_button.show()

    @Slot()
    def _move_left(self) -> None:
        scroll_bar = self.tab_container.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() - button_size().width() * 2)

    @Slot()
    def _move_right(self) -> None:
        scroll_bar = self.tab_container.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() + button_size().width() * 2)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._check_size()


class AbstractStackedTabWidget(QWidget):
    """A custom class that behaves like a QTabWidget"""

    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, f)
        self.setAcceptDrops(True)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self.tab_bar = self._new_tab_bar()
        self._layout.addWidget(self.tab_bar)
        self.stacked_widget = QStackedWidget()
        self._layout.addWidget(self.stacked_widget)

        self.tab_bar.tab_changed.connect(self.stacked_widget.setCurrentIndex)
        self.tab_bar.add_clicked.connect(self._add)

    def _new_tab_bar(self) -> AbstractTabBar:
        raise NotImplementedError

    @Slot()
    def _add(self) -> None:
        # from PySide6.QtWidgets import QLabel
        # i = random.randint(0, 9)
        # self.add_tab(QLabel(f"Test Widget {i}"), "test" + "a"*random.randint(0, 20) + str(i))
        pass

    def _validate_page(
        self, page: TabWidget
    ) -> tuple[str, Optional[QIcon]]:
        with DisplayException(f"Error in {page.__class__}"):
            if not isinstance(page, TabWidget):
                raise TypeError(
                    f"Page of type {type(page)} must be an instance of TabWidget"
                )
            name = page.name
            icon = page.icon
            if not isinstance(name, str):
                raise TypeError("Page name is invalid")
            if not (icon is None or isinstance(icon, QIcon)):
                raise TypeError("Page icon is invalid")
        return name, icon

    def add_page(self, page: TabWidget) -> None:
        name, icon = self._validate_page(page)
        self.tab_bar.add_tab(name, icon)
        self.stacked_widget.addWidget(page)

    def insert_page(self, index: int, page: TabWidget) -> None:
        name, icon = self._validate_page(page)
        self.tab_bar.insert_tab(index, name, icon)
        self.stacked_widget.insertWidget(index, page)

    def remove_page(self, index: int) -> TabWidget:
        self.tab_bar.remove_tab(index)
        widget = self.stacked_widget.widget(index)
        assert isinstance(widget, TabWidget)
        self.stacked_widget.removeWidget(widget)
        widget.setParent(None)
        # clean_up_widgets(self)
        return widget

    def clean_up(self) -> None:
        """
        A tab gets closed on a window
        If it was the last tab in the window
            If the tab widget is the last tab widget in the main window
        destroy the tab widget
        """
        if self.count():
            return

        splitter_widget = self.splitter

        if splitter_widget.count() == 2:
            # Remove the tab widget
            self.setParent(None)
            self.hide()
            self.deleteLater()

            grandparent_splitter_widget = splitter_widget.parent()
            if not isinstance(grandparent_splitter_widget, RecursiveSplitter):
                raise RuntimeError

            widget = splitter_widget.widget(0)
            grandparent_splitter_widget.replaceWidget(
                grandparent_splitter_widget.indexOf(splitter_widget), widget
            )

        elif splitter_widget.count() == 1:
            self._on_last_removed()
        else:
            raise RuntimeError

        # if isinstance(tab_widget, AbstractStackedTabWidget):
        #     if not tab_widget.count():
        #         # If there are no tabs in the stacked tab widget
        #         splitter_widget = tab_widget.splitter
        #         if isinstance(splitter_widget.parent(), main_window.AmuletMainWindow) and splitter_widget.count() == 1:
        #             # If this widget is the last AbstractStackedTabWidget in the AmuletMainWindow and has no tabs, open the default tab
        #             # TODO: add the default page
        #             print("add page")
        #         else:
        #             tab_widget.setParent(None)
        #             tab_widget.hide()
        #             tab_widget.deleteLater()
        #             clean_up_widgets(splitter_widget)
        # elif isinstance(tab_widget, RecursiveSplitter):
        #     parent = tab_widget.parent()
        #     if tab_widget.count() == 0:
        #         if isinstance(parent, sub_window.AmuletSubWindow):
        #             # widget.parent().hide()
        #             parent.deleteLater()
        #         else:
        #             raise RuntimeError
        #     elif tab_widget.count() == 1 and isinstance(parent, RecursiveSplitter):
        #         # If the widget only has one item in it them move the item into the parent splitter
        #         tab_widget = tab_widget.widget(0)
        #         if not isinstance(tab_widget, AbstractStackedTabWidget):
        #             raise RuntimeError
        #         index = parent.indexOf(tab_widget)
        #         parent.replaceWidget(index, tab_widget)
        #         tab_widget.setParent(None)
        #         tab_widget.hide()
        #         tab_widget.deleteLater()

    def _on_last_removed(self) -> None:
        raise NotImplementedError

    def count(self) -> int:
        return self.tab_bar.count()

    def current_index(self) -> int:
        return self.tab_bar.current_index()

    @property
    def splitter(self) -> RecursiveSplitter:
        parent = self.parent()
        if not isinstance(parent, RecursiveSplitter):
            raise RuntimeError(
                "Parent of AbstractStackedTabWidget must be RecursiveSplitter"
            )
        return parent


class RecursiveSplitter(QSplitter):
    @overload
    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None) -> None:
        ...
    @overload
    def __init__(self, parent: QWidget | None = None) -> None:
        ...
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setChildrenCollapsible(False)

    def addWidget(self, widget: Union[AbstractStackedTabWidget, RecursiveSplitter]) -> None:
        if not isinstance(widget, (AbstractStackedTabWidget, RecursiveSplitter)):
            raise TypeError(
                "widget must be an instance of TabArea or RecursiveSplitter"
            )
        super().addWidget(widget)

    def insertWidget(
        self, index: int, widget: Union[AbstractStackedTabWidget, RecursiveSplitter]
    ) -> None:
        if not isinstance(widget, (AbstractStackedTabWidget, RecursiveSplitter)):
            raise TypeError(
                "widget must be an instance of TabArea or RecursiveSplitter"
            )
        super().insertWidget(index, widget)
