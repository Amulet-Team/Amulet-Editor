from PySide6.QtWidgets import QWidget, QVBoxLayout

from amulet.core.block import BlockStack

from ._block_edit import BlockEdit


class BlockStackEdit(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)

        self._base_block = BlockEdit()
        self._layout.addWidget(self._base_block)

        # self._extra_block = BlockEdit()

    def get_block_stack(self) -> BlockStack:
        # return BlockStack(self._base_block.block, self._extra_block.block)
        return BlockStack(self._base_block.get_block())

    def set_block_stack(self, block_stack: BlockStack) -> None:
        self._base_block.set_block(block_stack.base_block)
        # extra_blocks = block_stack.extra_blocks
        # if extra_blocks:
