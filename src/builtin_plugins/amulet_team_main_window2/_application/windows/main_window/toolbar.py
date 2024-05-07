from typing import Optional, Callable
from threading import RLock
import traceback

from shiboken6 import isValid
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup

from amulet_editor.models.widgets import ADragContainer
from amulet_editor.models.widgets.traceback_dialog import display_exception

from amulet_editor.models.widgets._icon import ATooltipIconButton


class ButtonProxy:
    """
    This class is a proxy for a button in the toolbar.
    This is returned by the constructor for the button.
    You must store a reference to this in your plugin otherwise the button will be deleted.
    This is also used to access and remove the button.
    """

    def __init__(self, button: ATooltipIconButton):
        self.__button = button
        self.__callback = None

    def __del__(self):
        self.delete()

    def delete(self):
        """Delete the button"""
        if isValid(self.__button):
            self.__button.deleteLater()

    def set_icon(self, icon_path: str):
        self.__button.setIcon(icon_path)

    def set_name(self, name: str):
        self.__button.setToolTip(name)

    def set_callback(self, callback: Callable[[], None] = None):
        def on_click(evt):
            if callback is not None:
                try:
                    callback()
                except Exception as e:
                    display_exception(
                        title=f"Error running {callback}",
                        error=str(e),
                        traceback=traceback.format_exc(),
                    )

        if self.__callback is not None:
            self.__button.clicked.disconnect(self.__callback)
        self.__callback = on_click
        self.__button.clicked.connect(on_click)

    def click(self):
        self.__button.click()


class ToolBar(QFrame):
    """
    A toolbar is a strip of buttons.
    The first half can be rearranged and the second half are fixed.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        f: Qt.WindowType = Qt.WindowType.Widget,
        orientation=Qt.Orientation.Vertical,
    ):
        super().__init__(parent, f)

        layout_cls = {
            Qt.Orientation.Vertical: QVBoxLayout,
            Qt.Orientation.Horizontal: QHBoxLayout,
        }[orientation]

        self._lyt_main = layout_cls()
        self._lyt_main.setSpacing(5)
        self._lyt_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._lyt_main)

        self._wgt_dynamic_tools = ADragContainer(self, orientation)
        self._lyt_main.addWidget(self._wgt_dynamic_tools)

        self._lyt_fixed_tools = layout_cls()
        self._lyt_fixed_tools.addStretch()
        self._lyt_main.addLayout(self._lyt_fixed_tools)

        self._button_group = QButtonGroup()
        self._lock = RLock()

    def add_button(
        self,
        sticky=False,
        static=False,
    ):
        """
        Add a static button.
        This is reserved for internal use only.

        :param sticky: If True, the button will stick down when pressed.
        :param static: If True, the button will be in a different section and can't be moved.
        """
        button = ATooltipIconButton()
        button.setFixedSize(QSize(40, 40))
        button.setIconSize(QSize(30, 30))

        if sticky:
            button.setCheckable(True)
            self._button_group.addButton(button)

        if static:
            self._lyt_fixed_tools.insertWidget(1, button)
        else:
            self._wgt_dynamic_tools.add_item(button)

        return ButtonProxy(button)
