from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget


class ADragContainer(QWidget):
    """
    Generic list sorting handler.
    """

    # orderChanged = Signal(list)

    def __init__(
        self,
        parent: QWidget = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
    ):
        super().__init__(parent)
        self.setMouseTracking(True)

        self._layout = {
            Qt.Orientation.Horizontal: QHBoxLayout,
            Qt.Orientation.Vertical: QVBoxLayout,
        }[orientation](self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._drag = None

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._drag is None:
                for i in range(self._layout.count()):
                    child = self._layout.itemAt(i).widget()
                    if child.underMouse():
                        self._drag = child
                        break
            if self._drag is not None:
                point = event.position().toPoint()
                for i in range(self._layout.count()):
                    child = self._layout.itemAt(i).widget()
                    rect = child.rect()
                    rect.moveTo(child.pos())
                    if rect.contains(point):
                        self._layout.removeWidget(self._drag)
                        self._layout.insertWidget(i, self._drag)
                        break
        else:
            self._drag = None

    def add_item(self, item: QWidget):
        self._layout.addWidget(item)
