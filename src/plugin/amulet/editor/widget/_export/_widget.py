from PySide6.QtWidgets import QVBoxLayout

from plugin.amulet.editor.dock.widget import DockWidget

ExportWidgetIdentifier = "amulet.editor.ExportWidget"


class ExportWidget(DockWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    @property
    def title(self) -> str:
        return "Export"
