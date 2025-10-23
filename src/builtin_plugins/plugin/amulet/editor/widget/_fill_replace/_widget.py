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

from plugin.amulet.editor.widget.abc import TabWidget

from ._block_select import BlockSelect


FillReplaceWidgetIdentifier = "amulet.editor.FillReplaceWidget"


class FillWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._block_stack_select = BlockSelect()
        self._layout.addWidget(self._block_stack_select)


class FindWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._find_label = QLabel("Find")
        self._find_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._find_label.setStyleSheet("font-size: 15px")
        self._layout.addWidget(self._find_label)

        self._block_stack_select = BlockSelect(False)
        self._layout.addWidget(self._block_stack_select)

        self._splitter = QFrame()
        self._splitter.setFrameShape(QFrame.Shape.HLine)
        self._layout.addWidget(self._splitter)

        self._replace_label = QLabel("Replace")
        self._replace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._replace_label.setStyleSheet("font-size: 15px")
        self._layout.addWidget(self._replace_label)


class FillReplaceWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()

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

        self._find = FindWidget()
        self._layout.addWidget(self._find)

        self._fill_widget = FillWidget()
        self._layout.addWidget(self._fill_widget)

        self._layout.addStretch(1)

        self._fill_button.clicked.connect(self._fill_clicked)
        self._replace_button.clicked.connect(self._replace_clicked)
        self._fill_button.click()

    @property
    def title(self) -> str:
        return "Fill and Replace"

    def _fill_clicked(self) -> None:
        self._find.hide()

    def _replace_clicked(self) -> None:
        self._find.show()
