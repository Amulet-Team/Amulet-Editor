from typing import Callable
import traceback
from weakref import finalize, WeakMethod

from PySide6.QtCore import QSize, Qt, QObject, QEvent, QRect, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QButtonGroup,
    QScrollArea,
)

from plugin.amulet.editor._toolbar_button import ToolbarButton
from amulet.app.exception import display_exception


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
        :param on_delete: A function to call just before deleting the button.
        """
        self._button: ToolbarButton | None = button
        self._on_click: Callable[[], None] | None = None
        weak_destroy = WeakMethod(self._destroy)
        self._finalise = finalize(
            self, lambda: (destroy := weak_destroy()) and destroy()
        )

    def _get_button(self) -> ToolbarButton:
        if self._button is None:
            raise RuntimeError("The button has already been destroyed.")
        return self._button

    def _destroy(self) -> None:
        self._get_button().deleteLater()
        self._button = None

    def __del__(self) -> None:
        self._finalise()

    def delete(self) -> None:
        """Delete the button"""
        self._finalise()

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


class DragContainer(QScrollArea):
    """A rearrangeable list of buttons."""

    # orderChanged = Signal(list)

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

        # self.setMouseTracking(True)

        self._widget = QWidget()

        layout_cls = LayoutCls[orientation]

        self._container_layout = layout_cls(self._widget)
        self._container_layout.setContentsMargins(0, 0, 0, 0)

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
                    point = event.globalPos()
                    for i in range(self._layout.count()):
                        item = self._layout.itemAt(i)
                        if item is None:
                            continue
                        child = item.widget()
                        if child is None:
                            continue
                        if QRect(child.mapToGlobal(QPoint()), child.size()).contains(
                            point
                        ):
                            if self._dragged_widget is child:
                                break
                            self._layout.removeWidget(self._dragged_widget)
                            self._layout.insertWidget(i, self._dragged_widget)
                            self._dragged = True
                            break
        return super().eventFilter(obj, event)

    def add_item(self, item: QWidget) -> None:
        self._layout.addWidget(item)
        item.installEventFilter(self)

    def sizeHint(self) -> QSize:
        return self._size_hint

    def minimumSizeHint(self) -> QSize:
        return self._size_hint



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

        layout_cls = LayoutCls[orientation]

        self._lyt_main = layout_cls(self)
        self._lyt_main.setSpacing(5)
        self._lyt_main.setContentsMargins(0, 0, 0, 0)

        self._wgt_layout_buttons = DragContainer(self, orientation)
        self._lyt_main.addWidget(self._wgt_layout_buttons, 1)

        self._lyt_static_buttons = layout_cls()
        self._lyt_main.addLayout(self._lyt_static_buttons)

        self._layout_button_group = QButtonGroup()

    def add_layout_button(self) -> ToolbarButton:
        """Add a button to the toolbar."""
        button = ToolbarButton()
        button.setFixedSize(QSize(ButtonSize, ButtonSize))
        button.setIconSize(QSize(IconSize, IconSize))
        button.setCheckable(True)
        self._layout_button_group.addButton(button)
        self._wgt_layout_buttons.add_item(button)
        return button

    def uncheck_layout_buttons(self) -> None:
        button = self._layout_button_group.checkedButton()
        if button is not None:
            button.setChecked(False)

    def add_static_button(self) -> ToolbarButton:
        """Add a button to the toolbar."""
        button = ToolbarButton()
        button.setFixedSize(QSize(ButtonSize, ButtonSize))
        button.setIconSize(QSize(IconSize, IconSize))
        self._lyt_static_buttons.insertWidget(0, button)
        return button
