from PySide6.QtWidgets import QVBoxLayout, QLabel

from plugin.amulet.editor.widget.abc import TabWidget


ClipboardWidgetIdentifier = "amulet.editor.ClipboardWidget"


class ClipboardWidget(TabWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("This will display the copied structures.")
        self._layout.addWidget(self._label)

    @property
    def title(self) -> str:
        return "Clipboard"
