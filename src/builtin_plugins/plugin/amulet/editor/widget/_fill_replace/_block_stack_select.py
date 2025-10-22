from PySide6.QtWidgets import QWidget, QVBoxLayout

from ._block_select import BlockSelect


class BlockStackSelect(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
