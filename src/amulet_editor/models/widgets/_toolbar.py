from typing import Optional, Callable
from threading import RLock

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout

from amulet_editor.models.widgets import ADragContainer

from ._icon import ATooltipIconButton


class AToolBar(QFrame):
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
        self._wgt_dynamic_tools.setObjectName("_wgt_dynamic_tools")
        self._lyt_main.addWidget(self._wgt_dynamic_tools)

        self._lyt_fixed_tools = layout_cls()
        self._lyt_fixed_tools.setObjectName("_lyt_fixed_tools")
        self._lyt_fixed_tools.addStretch()
        self._lyt_main.addLayout(self._lyt_fixed_tools)

        self._buttons: dict[str, ATooltipIconButton] = {}
        self._lock = RLock()

    def _make_button(
        self, uid: str, icon: str, name: str, callback: Callable[[], None] = None
    ) -> ATooltipIconButton:
        if uid in self._buttons:
            raise ValueError(
                f"A button with unique identifier {uid} has already been registered"
            )

        button = ATooltipIconButton(icon, self)
        button.setToolTip(name)
        button.setFixedSize(QSize(40, 40))
        button.setIconSize(QSize(30, 30))

        def on_click(evt):
            if callback is not None:
                try:
                    callback()
                except Exception:
                    pass

        button.clicked.connect(on_click)
        self._buttons[uid] = button
        return button

    def add_static_button(
        self, uid: str, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add a static button.
        This is reserved for internal use only.

        :param uid: A unique identifier. Used to remove this button.
        :param icon: The icon the button should use.
        :param name: The name of the button in the tool tip.
        :param callback: The function to call when the button is clicked.
        """
        with self._lock:
            button = self._make_button(uid, icon, name, callback)
            self._lyt_fixed_tools.insertWidget(1, button)

    def add_dynamic_button(
        self, uid: str, icon: str, name: str, callback: Callable[[], None] = None
    ):
        """
        Add a dynamic button.
        Plugins can add their own dynamic buttons.

        :param uid: A unique identifier. Used to remove this button.
        :param icon: The icon the button should use.
        :param name: The name of the button in the tool tip.
        :param callback: The function to call when the button is clicked.
        """
        with self._lock:
            button = self._make_button(uid, icon, name, callback)
            self._wgt_dynamic_tools.add_item(button)

    def remove_button(self, uid: str):
        """
        Remove a button from the toolbar

        :param uid: The uid of the button to remove.
        """
        with self._lock:
            button = self._buttons.pop(uid)
            button.deleteLater()

    def activate(self, uid: str):
        """
        Visually show that a tool is active.
        All other tools will be visually disabled.
        This is only a visual update and does not produce any events.

        :param uid: The uid of the button to activate.
        """
        with self._lock:
            new_button = self._buttons[uid]
            for button in self._buttons.values():
                if button is not new_button:
                    button.setChecked(False)
                    button.setCheckable(False)
            new_button.setCheckable(True)
            new_button.setChecked(True)
