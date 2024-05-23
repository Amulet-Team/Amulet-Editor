from typing import Callable
from threading import RLock
import traceback
from weakref import finalize

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup

from amulet.utils.weakref import CallableWeakMethod

from amulet_editor.models.widgets import ADragContainer, ATooltipIconButton
from amulet_editor.models.widgets.traceback_dialog import display_exception


class ButtonProxy:
    """
    This class is a proxy for a button in the toolbar.
    This is returned by the constructor for the button.
    You must store a reference to this in your plugin otherwise the button will be deleted.
    This is also used to access and remove the button.
    """

    def __init__(self, button: ATooltipIconButton) -> None:
        """
        :param button: The button to wrap.
        :param on_delete: A function to call just before deleting the button.
        """
        self._button: ATooltipIconButton | None = button
        self._on_click: Callable[[], None] | None = None
        self._finalise = finalize(self, CallableWeakMethod(self._destroy))

    def _get_button(self) -> ATooltipIconButton:
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


class ToolBar(QFrame):
    """
    A toolbar is a strip of buttons.
    The first half can be rearranged and the second half are fixed.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        f: Qt.WindowType = Qt.WindowType.Widget,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
    ) -> None:
        super().__init__(parent, f)

        layout_cls = {
            Qt.Orientation.Vertical: QVBoxLayout,
            Qt.Orientation.Horizontal: QHBoxLayout,
        }[orientation]

        self._lyt_main = layout_cls()
        self._lyt_main.setSpacing(5)
        self._lyt_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._lyt_main)

        self._wgt_layout_buttons = ADragContainer(self, orientation)
        self._lyt_main.addWidget(self._wgt_layout_buttons)

        self._lyt_static_buttons = layout_cls()
        self._lyt_static_buttons.addStretch()
        self._lyt_main.addLayout(self._lyt_static_buttons)

        self._layout_button_group = QButtonGroup()
        self._lock = RLock()

    def add_layout_button(self) -> ATooltipIconButton:
        """Add a button to the toolbar."""
        button = ATooltipIconButton()
        button.setFixedSize(QSize(40, 40))
        button.setIconSize(QSize(30, 30))
        button.setCheckable(True)
        self._layout_button_group.addButton(button)
        self._wgt_layout_buttons.add_item(button)
        return button

    def uncheck_layout_buttons(self) -> None:
        self._layout_button_group.checkedButton().setChecked(False)

    def add_static_button(self) -> ATooltipIconButton:
        """Add a button to the toolbar."""
        button = ATooltipIconButton()
        button.setFixedSize(QSize(40, 40))
        button.setIconSize(QSize(30, 30))
        self._lyt_static_buttons.insertWidget(1, button)
        return button
