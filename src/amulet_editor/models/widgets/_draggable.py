from typing import Any
import warnings

from amulet_editor.models.widgets._icon import QIconButton
from PySide6.QtCore import QCoreApplication, QEvent, QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLayout, QVBoxLayout, QWidget


class QDragIconButton(QIconButton):
    def __init__(self, *args, **kwargs) -> None:
        warnings.warn("QDragIconButton is depreciated.", DeprecationWarning)
        super().__init__(*args, **kwargs)

        self.data = self._icon_name

    def setData(self, data) -> None:
        self.data = data

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

            mouseReleaseEvent = QMouseEvent(
                QEvent.MouseButtonRelease,
                self.cursor().pos(),
                Qt.LeftButton,
                Qt.LeftButton,
                Qt.NoModifier,
            )
            QCoreApplication.postEvent(self, mouseReleaseEvent)

        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        return super().mouseReleaseEvent(event)


class QDragContainer(QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs) -> None:
        warnings.warn("QDragContainer is depreciated. Use ADragContainer instead.", DeprecationWarning)
        super().__init__()
        self.setAcceptDrops(True)

        self.__orientation__ = orientation
        self.__layout__ = (
            QVBoxLayout()
            if self.__orientation__ == Qt.Orientation.Vertical
            else QHBoxLayout()
        )

        self.setLayout(self.__layout__)

    def layout(self) -> QLayout:
        return self.__layout__

    def addItem(self, item) -> None:
        self.__layout__.addWidget(item)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        pos = event.pos()
        widget = event.source()

        for n in range(self.__layout__.count()):
            w = self.__layout__.itemAt(n).widget()

            drop_here = (
                pos.y() < w.y() + w.size().height() // 2
                if self.__orientation__ == Qt.Orientation.Vertical
                else pos.x() < w.x() + w.size().width() // 2
            )

            if drop_here:
                self.__layout__.insertWidget(n, widget)
                self.orderChanged.emit(self.getItemData())
                break
        else:
            self.__layout__.addWidget(widget)
            self.orderChanged.emit(self.getItemData())

        event.accept()

        mouseReleaseEvent = QMouseEvent(
            QEvent.MouseButtonRelease,
            self.cursor().pos(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        QCoreApplication.postEvent(widget, mouseReleaseEvent)

    def getItemData(self) -> list[Any]:
        return [
            self.__layout__.itemAt(idx).widget().data
            for idx in range(self.__layout__.count())
        ]


class ADragContainer(QWidget):
    """
    Generic list sorting handler.
    """

    # orderChanged = Signal(list)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Vertical, parent: QWidget = None):
        super().__init__(parent)
        self.setMouseTracking(True)

        self._layout = {
            Qt.Orientation.Horizontal: QHBoxLayout,
            Qt.Orientation.Vertical: QVBoxLayout
        }[orientation](self)

        self._drag = None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
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
