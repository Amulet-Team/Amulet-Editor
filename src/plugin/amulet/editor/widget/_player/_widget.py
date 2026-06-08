from PySide6.QtWidgets import QVBoxLayout, QLabel

from amulet.level.abc import Level

from plugin.amulet.editor.dock.widget import DockWidget

PlayerWidgetIdentifier = "amulet.editor.PlayerWidget"


class PlayerWidget(DockWidget):
    def __init__(self, level: Level) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("This will display player info.")
        self._layout.addWidget(self._label)

    @property
    def title(self) -> str:
        return "Player"
