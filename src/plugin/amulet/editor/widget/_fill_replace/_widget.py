from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QWidget,
    QLabel,
    QFrame,
)

from amulet.core.block import Block
from amulet.level.abc import Level

from plugin.amulet.editor.dock.widget import DockWidget

from ._block_select import BlockSelect
from ._op import fill_block

FillReplaceWidgetIdentifier = "amulet.editor.FillReplaceWidget"


class FillWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._block_select = BlockSelect()
        self._layout.addWidget(self._block_select)

    def get_block(self) -> Block:
        return self._block_select.get_block()


class FindWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._find_label = QLabel("Find")
        self._find_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._find_label.setStyleSheet("font-size: 15px")
        self._layout.addWidget(self._find_label)

        self._block_select = BlockSelect(False)
        self._layout.addWidget(self._block_select)

        self._splitter = QFrame()
        self._splitter.setFrameShape(QFrame.Shape.HLine)
        self._layout.addWidget(self._splitter)

        self._replace_label = QLabel("Replace")
        self._replace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._replace_label.setStyleSheet("font-size: 15px")
        self._layout.addWidget(self._replace_label)

    def get_block(self) -> Block:
        return self._block_select.get_block()


class FillReplaceWidget(DockWidget):
    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = level

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._button_layout = QHBoxLayout()
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self._button_layout.setSpacing(0)
        self._layout.addLayout(self._button_layout)

        self._button_group = QButtonGroup()
        self._button_group.setExclusive(True)

        self._fill_button = QPushButton("Fill")
        self._fill_button.setCheckable(True)
        self._button_group.addButton(self._fill_button)
        self._button_layout.addWidget(self._fill_button)

        self._replace_button = QPushButton("Replace")
        self._replace_button.setCheckable(True)
        self._button_group.addButton(self._replace_button)
        self._button_layout.addWidget(self._replace_button)

        self._find_widget = FindWidget()
        self._layout.addWidget(self._find_widget)

        self._fill_widget = FillWidget()
        self._layout.addWidget(self._fill_widget)

        self._run_button = QPushButton("Run")
        self._run_button.clicked.connect(self._run_clicked)
        self._layout.addWidget(self._run_button)

        self._layout.addStretch(1)

        self._fill_button.clicked.connect(self._fill_clicked)
        self._replace_button.clicked.connect(self._replace_clicked)
        self._fill_button.click()

    @property
    def title(self) -> str:
        return "Fill and Replace"

    def _fill_clicked(self) -> None:
        self._find_widget.hide()

    def _replace_clicked(self) -> None:
        self._find_widget.show()

    def _run_clicked(self) -> None:
        if self._fill_button.isChecked():
            find_block = None
        else:
            find_block = self._find_widget.get_block()
        fill_block(self._level, self._fill_widget.get_block(), find_block)
