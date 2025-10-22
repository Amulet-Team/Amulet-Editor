from __future__ import annotations

import traceback

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
    QPushButton,
    QMessageBox,
)

from amulet.utils.lock import ThreadAccessMode, ThreadShareMode

from amulet.core.chunk.component import BlockComponent
from amulet.core.chunk import ChunkLoadError, ChunkDoesNotExist

from amulet.app.exception import display_exception, CatchExceptionDialog

from plugin.amulet.editor.widget.abc import TabWidget
from plugin.amulet.level import get_main_level

from ._block_edit import BlockEdit
from ._block_stack_edit import BlockStackEdit


BlockEditWidgetIdentifier = "amulet.editor.BlockEdit"


class BlockEditWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._x_input = QSpinBox(minimum=-30_000_000, maximum=30_000_000)
        self._layout.addWidget(self._x_input)
        self._y_input = QSpinBox(minimum=-30_000_000, maximum=30_000_000)
        self._layout.addWidget(self._y_input)
        self._z_input = QSpinBox(minimum=-30_000_000, maximum=30_000_000)
        self._layout.addWidget(self._z_input)

        self._button_layout = QHBoxLayout()
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._button_layout)

        self._get_block_button = QPushButton("Get Block")
        self._get_block_button.clicked.connect(self._get_block)
        self._button_layout.addWidget(self._get_block_button)

        self._set_block_button = QPushButton("Set Block")
        self._set_block_button.clicked.connect(self._set_block)
        self._button_layout.addWidget(self._set_block_button)
        self._set_block_button.setEnabled(False)

        self._block_edit = BlockStackEdit()
        self._layout.addWidget(self._block_edit)
        self._block_edit.hide()

        self._x_input.valueChanged.connect(self._disable)
        self._y_input.valueChanged.connect(self._disable)
        self._z_input.valueChanged.connect(self._disable)

        self._layout.addStretch(1)

        self._container_layout = QHBoxLayout(self)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.addLayout(self._layout)
        self._container_layout.addStretch(1)

    def _disable(self) -> None:
        self._block_edit.hide()
        self._set_block_button.setEnabled(False)

    def _enable(self) -> None:
        self._block_edit.show()
        self._set_block_button.setEnabled(True)

    @property
    def title(self) -> str:
        return "Block Editor"

    def _get_block(self) -> None:
        with CatchExceptionDialog("Error getting block."):
            x = self._x_input.value()
            y = self._y_input.value()
            z = self._z_input.value()
            level = get_main_level()
            if level is None:
                return
            sub_chunk_size = level.sub_chunk_size
            cx = x // sub_chunk_size
            cz = z // sub_chunk_size
            with level.lock(
                thread_mode=(ThreadAccessMode.Read, ThreadShareMode.SharedReadWrite)
            ):
                dimension = level.get_dimension("minecraft:overworld")
                chunk_handle = dimension.get_chunk_handle(cx, cz)
                try:
                    with chunk_handle.lock(
                        thread_mode=(
                            ThreadAccessMode.Read,
                            ThreadShareMode.SharedReadWrite,
                        )
                    ):
                        chunk = chunk_handle.get_chunk([BlockComponent.ComponentID])
                except ChunkDoesNotExist:
                    msg_box = QMessageBox(text="This chunk does not exist.")
                    msg_box.exec()
                except ChunkLoadError as e:
                    display_exception(
                        "Error loading chunk", str(e), traceback.format_exc()
                    )
                else:
                    if isinstance(chunk, BlockComponent):
                        block_storage = chunk.block_storage
                        sections = block_storage.sections
                        if sections.array_shape != (
                            sub_chunk_size,
                            sub_chunk_size,
                            sub_chunk_size,
                        ):
                            raise RuntimeError("Unsupported array shape")
                        cy = y // sub_chunk_size
                        if cy not in sections:
                            msg_box = QMessageBox(text="This sub-chunk does not exist.")
                            msg_box.exec()
                        section = sections[cy]
                        dx = x - cx * sub_chunk_size
                        dy = y - cy * sub_chunk_size
                        dz = z - cz * sub_chunk_size
                        block_index = section[dx, dy, dz]
                        block_stack = block_storage.palette.index_to_block_stack(
                            block_index
                        )
                        self._block_edit.set_block_stack(block_stack)
                        self._enable()

    def _set_block(self) -> None:
        with CatchExceptionDialog("Error getting block."):
            x = self._x_input.value()
            y = self._y_input.value()
            z = self._z_input.value()
            block_stack = self._block_edit.get_block_stack()
            level = get_main_level()
            if level is None:
                return
            sub_chunk_size = level.sub_chunk_size
            cx = x // sub_chunk_size
            cz = z // sub_chunk_size
            with level.lock(
                thread_mode=(
                    ThreadAccessMode.ReadWrite,
                    ThreadShareMode.SharedReadWrite,
                )
            ):
                dimension = level.get_dimension("minecraft:overworld")
                chunk_handle = dimension.get_chunk_handle(cx, cz)
                with chunk_handle.lock(
                    thread_mode=(
                        ThreadAccessMode.ReadWrite,
                        ThreadShareMode.SharedReadOnly,
                    )
                ):
                    try:
                        chunk = chunk_handle.get_chunk([BlockComponent.ComponentID])
                    except ChunkDoesNotExist:
                        msg_box = QMessageBox(text="This chunk does not exist.")
                        msg_box.exec()
                    except ChunkLoadError as e:
                        display_exception(
                            "Error loading chunk", str(e), traceback.format_exc()
                        )
                    else:
                        if isinstance(chunk, BlockComponent):
                            block_storage = chunk.block_storage
                            sections = block_storage.sections
                            if sections.array_shape != (
                                sub_chunk_size,
                                sub_chunk_size,
                                sub_chunk_size,
                            ):
                                raise RuntimeError("Unsupported array shape")
                            cy = y // sub_chunk_size
                            if cy not in sections:
                                msg_box = QMessageBox(
                                    text="This sub-chunk does not exist."
                                )
                                msg_box.exec()
                            section = sections[cy]
                            dx = x - cx * sub_chunk_size
                            dy = y - cy * sub_chunk_size
                            dz = z - cz * sub_chunk_size

                            block_index = block_storage.palette.block_stack_to_index(
                                block_stack
                            )
                            section[dx, dy, dz] = block_index
                            chunk_handle.set_chunk(chunk)
