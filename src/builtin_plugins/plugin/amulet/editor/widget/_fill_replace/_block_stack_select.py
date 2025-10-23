from PySide6.QtWidgets import QWidget, QVBoxLayout

from ._block_select import BlockSelect


class BlockStackSelect(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._base_block = BlockSelect()
        self._layout.addWidget(self._base_block)
