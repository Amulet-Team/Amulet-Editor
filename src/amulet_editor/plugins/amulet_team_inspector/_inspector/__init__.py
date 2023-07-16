from typing import Optional
from weakref import ref

from PySide6.QtWidgets import QTreeWidgetItem, QApplication, QWidget
from PySide6.QtCore import QObject, QRect, QEvent, QPoint
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QIcon

from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.data.build import get_resource

from ._inspector import Ui_InspectionTool


class TreeWidgetItem(QTreeWidgetItem):
    @classmethod
    def create(cls, widget: QObject) -> Optional[QTreeWidgetItem]:
        if isinstance(widget, InspectorTool):
            return None
        else:
            return cls(widget)

    def __init__(self, widget: QObject):
        super().__init__([str(widget)])
        self.widget = ref(widget)
        for child in widget.children():
            item = self.create(child)
            self.addChild(item)


class CustomDraw(QObject):
    def __init__(self, target: QWidget):
        super().__init__(target)
        self.target = target
        self.background = target.grab()
        self.target.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.target and event.type() == QEvent.Type.Paint:
            painter = QPainter(self.target)
            painter.drawPixmap(QPoint(0, 0), self.background)
            painter.fillRect(
                QRect(0, 0, painter.device().width(), painter.device().height()),
                QColor(115, 215, 255, 128),
            )
            painter.end()
            return True
        return super().eventFilter(obj, event)


class InspectorTool(Ui_InspectionTool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inspect = False
        self._highlight: Optional[tuple[QWidget, QObject]] = None

        self.inspect_button.setIcon(QIcon(get_resource("icons/tabler/click.svg")))
        self.reload_button.setIcon(QIcon(get_resource("icons/tabler/refresh.svg")))

        self.inspect_button.clicked.connect(self.inspect)
        self.reload_button.clicked.connect(self.reload)
        self.run_button.clicked.connect(self.run_code)
        self.reload()

    def reload(self):
        self.tree_widget.clear()
        for window in QApplication.topLevelWidgets():
            root = TreeWidgetItem.create(window)
            if root is not None:
                self.tree_widget.addTopLevelItem(root)
        if self.tree_widget.topLevelItemCount():
            self.tree_widget.topLevelItem(0)

    def inspect(self):
        self.setMouseTracking(True)
        self.grabMouse()
        self._inspect = True

    def _remove_highlight(self):
        if self._highlight is not None:
            widget, filt = self._highlight
            widget.removeEventFilter(filt)
            widget.update()
            self._highlight = None

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._inspect:
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

            filt = CustomDraw(widget)
            widget.update()
            self._highlight = widget, filt
        else:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if self._inspect:
            self._inspect = False
            self.releaseMouse()
            self.setMouseTracking(False)
            self._remove_highlight()
        else:
            super().mousePressEvent(event)

    def run_code(self):
        item = self.tree_widget.currentItem()
        if not isinstance(item, TreeWidgetItem):
            return
        obj = item.widget()
        if obj is None:
            print("Selected object no longer exists.")
        else:
            with DisplayException("Error running user code."):
                eval(self.code_editor.toPlainText(), {}, {"obj": obj})


_inspector = None


def show_inspector():
    global _inspector
    if _inspector is None:
        _inspector = InspectorTool()
        _inspector.show()
    _inspector.raise_()
