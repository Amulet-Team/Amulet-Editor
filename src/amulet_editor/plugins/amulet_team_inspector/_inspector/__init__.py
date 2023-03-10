from typing import Optional
from weakref import ref

from PySide6.QtWidgets import QTreeWidgetItem, QApplication
from PySide6.QtCore import QObject

from amulet_editor.models.widgets import DisplayException

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


class InspectorTool(Ui_InspectionTool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
