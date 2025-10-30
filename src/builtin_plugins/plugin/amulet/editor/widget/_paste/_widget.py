from PySide6.QtWidgets import QVBoxLayout, QLabel

from plugin.amulet.editor.widget.abc import TabWidget


PasteWidgetIdentifier = "amulet.editor.PasteWidget"


class PasteWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("This will display the structures being placed.")
        self._layout.addWidget(self._label)

    @property
    def title(self) -> str:
        return "Paste"
