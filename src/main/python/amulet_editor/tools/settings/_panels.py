from typing import Optional

from PySide6.QtWidgets import QWidget


class SettingsPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
