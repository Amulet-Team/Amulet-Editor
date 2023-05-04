from typing import Optional

from PySide6.QtWidgets import QWidget


class SettingsPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
