from PySide6.QtWidgets import QVBoxLayout, QLabel

from plugin.amulet.editor.widget.abc import TabWidget

PlayerWidgetIdentifier = "amulet.editor.PlayerWidget"


class PlayerWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("This will display player info.")
        self._layout.addWidget(self._label)

    @property
    def title(self) -> str:
        return "Player"
