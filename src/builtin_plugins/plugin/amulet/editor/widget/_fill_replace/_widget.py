from PySide6.QtWidgets import QVBoxLayout

from plugin.amulet.editor.widget.abc import TabWidget

from ._block_stack_select import BlockStackSelect


FillReplaceWidgetIdentifier = "amulet.editor.FillReplaceWidget"


class FillReplaceWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widget = BlockStackSelect()
        self._layout.addWidget(self._widget)

    @property
    def title(self) -> str:
        return "Fill and Replace"
