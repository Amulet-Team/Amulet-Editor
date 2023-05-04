from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget


class AmuletView(QObject):
    changed = Signal(QWidget)

    def __init__(self, widget: Optional[QWidget] = None):
        super().__init__()

        self.__widget__ = widget

    def widget(self) -> Optional[QWidget]:
        return self.__widget__

    def setWidget(self, widget: QWidget):
        self.__widget__ = widget
        self.changed.emit(self.__widget__)
