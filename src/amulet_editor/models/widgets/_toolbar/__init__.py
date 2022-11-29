from PySide6.QtCore import QSize

from ._toolbar import AToolBar_
from .._icon import ATooltipIconButton


class AToolBar(AToolBar_):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._static_tools: dict[str, ATooltipIconButton] = {}
        self._dynamic_tools: dict[str, ATooltipIconButton] = {}
        # self.add_static_button("amulet:settings", "settings.svg", "Settings")

    def _make_button(self, icon: str, name: str) -> ATooltipIconButton:
        button = ATooltipIconButton(icon, self)
        button.setToolTip(name)
        button.setCheckable(True)
        button.setFixedSize(QSize(40, 40))
        button.setIconSize(QSize(30, 30))
        return button

    def add_static_button(self, uid: str, icon: str, name: str):
        """
        Add a static button.
        This is reserved for internal use only.

        :param uid: A unique identifier. Used to remove this button.
        :param icon: The icon the button should use
        :param name: The name of the button in the tool tip.
        """
        if uid in self._static_tools:
            raise ValueError(f"A button with unique identifier {uid} has already been registered")
        button = self._make_button(icon, name)
        self._static_tools[uid] = button
        self._lyt_fixed_tools.insertWidget(1, button)

    def remove_static_button(self, uid: str):
        self._static_tools.pop(uid).deleteLater()

    def add_dynamic_button(self, uid: str, icon: str, name: str):
        """
        Add a dynamic button.
        Plugins can add their own dynamic buttons.

        :param uid: A unique identifier. Used to remove this button.
        :param icon: The icon the button should use
        :param name: The name of the button in the tool tip.
        """
        if uid in self._dynamic_tools:
            raise ValueError(f"A button with unique identifier {uid} has already been registered")
        button = self._make_button(icon, name)
        self._dynamic_tools[uid] = button
        self._wgt_dynamic_tools.add_item(button)

    def remove_dynamic_button(self, uid: str):
        self._dynamic_tools.pop(uid).deleteLater()
