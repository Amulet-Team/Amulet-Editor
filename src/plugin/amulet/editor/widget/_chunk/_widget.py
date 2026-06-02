from PySide6.QtWidgets import QVBoxLayout, QLabel

from plugin.amulet.editor.dock.widget import DockWidget

ChunkWidgetIdentifier = "amulet.editor.ChunkWidget"


class ChunkWidget(DockWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("This will display the chunk tools.")
        self._layout.addWidget(self._label)

    @property
    def title(self) -> str:
        return "Chunk"
