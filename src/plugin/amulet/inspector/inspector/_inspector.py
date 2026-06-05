from typing import Optional
from weakref import ref

from PySide6.QtWidgets import QTreeWidgetItem, QApplication, QWidget
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QIcon, QCloseEvent, QPaintEvent

from amulet.app.exception import CatchExceptionDialog
from plugin.tablericons import tablericons

from ._inspector_gui import InspectionToolGUI


class TreeWidgetItem(QTreeWidgetItem):
    @classmethod
    def create(cls, widget: QObject) -> Optional[QTreeWidgetItem]:
        if isinstance(widget, InspectorTool):
            return None
        else:
            return cls(widget)

    def __init__(self, widget: QObject) -> None:
        super().__init__([str(widget)])
        self.widget = ref(widget)
        for child in widget.children():
            item = self.create(child)
            if item is not None:
                self.addChild(item)


class Overlay(QWidget):
    """A class to implement cuboid highlighting."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.move(QPoint())
        self.resize(parent.size())
        self.show()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(QColor(115, 215, 255, 128))
        painter.setPen(QColor(115, 215, 255))
        painter.drawRect(self.rect())
        painter.end()


class InspectorTool(InspectionToolGUI):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        self._inspecting = False
        self._highlight: tuple[QWidget, Overlay] | None = None

        self.inspect_button.setIcon(QIcon(tablericons.outline.click))
        self.reload_button.setIcon(QIcon(tablericons.outline.refresh))

        self.inspect_button.clicked.connect(self._start_inspecting)
        self.reload_button.clicked.connect(self.reload)
        self.run_button.clicked.connect(self._run_code)
        self.reload()

    def closeEvent(self, event: QCloseEvent) -> None:
        global _inspector
        _inspector = None

    def reload(self) -> None:
        self.tree_widget.clear()
        for window in QApplication.topLevelWidgets():
            root = TreeWidgetItem.create(window)
            if root is not None:
                self.tree_widget.addTopLevelItem(root)
        if self.tree_widget.topLevelItemCount():
            self.tree_widget.topLevelItem(0)

    def _start_inspecting(self) -> None:
        self.setMouseTracking(True)
        self.grabMouse()
        self._inspecting = True

    def _remove_highlight(self) -> None:
        if self._highlight is not None:
            widget, overlay = self._highlight
            overlay.deleteLater()
            self._highlight = None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._inspecting:
            widget = QApplication.widgetAt(event.globalPosition().toPoint())
            if not widget:
                return
            if widget.topLevelWidget() is self:
                return

            if self._highlight is not None:
                if self._highlight[0] is widget:
                    return
                else:
                    self._remove_highlight()

            self._highlight = widget, Overlay(widget)
        else:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._inspecting:
            self._inspecting = False
            self.releaseMouse()
            self.setMouseTracking(False)
            self._remove_highlight()
        else:
            super().mousePressEvent(event)

    def _run_code(self) -> None:
        item = self.tree_widget.currentItem()
        if not isinstance(item, TreeWidgetItem):
            return
        obj = item.widget()
        if obj is None:
            print("Selected object no longer exists.")
        else:
            with CatchExceptionDialog("Error running user code.", suppress=False):
                exec(self.code_editor.toPlainText(), {}, {"self": obj})
