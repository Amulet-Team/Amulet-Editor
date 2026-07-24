import os
import sys
import subprocess
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, Qt, QCoreApplication
from PySide6.QtGui import QMouseEvent, QFont
from PySide6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QFileIconProvider,
    QMenu,
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
)

from amulet.nbt import read_nbt, java_encoding, NamedTag

from amulet.app.exception import CatchExceptionDialog

from amulet.level.java import JavaLevel

from plugin.amulet.nbt.widget import NBTWidget, TagType


class NBTDialog(QDialog):
    def __init__(self, tag: TagType | None = None) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)

        self._widget = NBTWidget(tag)
        self._layout.addWidget(self._widget)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Discard
        )
        self._layout.addWidget(self._buttons)

        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        self._buttons.button(QDialogButtonBox.StandardButton.Discard).clicked.connect(
            self.reject
        )

    def get_tag(self) -> TagType:
        return self._widget.get_tag()

    def set_tag(self, tag: TagType) -> None:
        self._widget.set_tag(tag)


class PathItem(QTreeWidgetItem):
    def __init__(self, parent: JavaLevelExplorer | PathItem, path: str) -> None:
        super().__init__(parent)
        self.path = path
        self.populated = False


class JavaLevelExplorer(QTreeWidget):
    def __init__(self, level: JavaLevel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._level = level

        font = QFont(
            [
                "Consolas",
                "Menlo",
                "DejaVu Sans Mono",
                "Liberation Mono",
                "Courier New",
                "Courier",
                "monospace",
            ]
        )
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)

        self._icon_provider = QFileIconProvider()
        self._root_node = PathItem(self, level.path)
        self._root_node.setText(0, level.path)
        self._root_node.setChildIndicatorPolicy(
            QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
        )

        self.itemExpanded.connect(self._expand_item)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._right_clicked)

    def reload(self) -> None:
        path = self._level.path
        if not os.path.isdir(path):
            return
        self._root_node.takeChildren()
        self._root_node.setExpanded(False)
        self._root_node.populated = False
        self.expandToDepth(0)

    def _expand_item(self, item: QTreeWidgetItem) -> None:
        with CatchExceptionDialog("Error expanding item"):
            if not isinstance(item, PathItem) or item.populated:
                return
            path = item.path
            if not os.path.isdir(path):
                return
            try:
                entries = sorted(
                    os.scandir(path),
                    key=lambda v: (v.name.lower(), v.name.swapcase()),
                )
            except OSError:
                return

            for entry in entries:
                child_item = PathItem(item, entry.path)
                child_item.setText(0, entry.name)
                child_item.setIcon(0, self._icon_provider.icon(QFileInfo(entry.path)))
                if entry.is_dir() and next((os.scandir(entry.path)), None) is not None:
                    child_item.setChildIndicatorPolicy(
                        QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                    )
            item.populated = True

    def _right_clicked(self, point: QPoint, /) -> None:
        item = self.itemAt(point)
        if isinstance(item, PathItem):
            path_item = item
            menu = QMenu(self)

            menu.addAction(
                QCoreApplication.translate(
                    "plugin.amulet.editor.JavaLevelExplorer", "open_in_explorer", None
                ),
                lambda: self._open_in_explorer(path_item),
            )

            if os.path.isfile(path_item.path) and path_item.path.endswith(
                (".dat", ".dat_old")
            ):
                menu.addAction(
                    QCoreApplication.translate(
                        "plugin.amulet.editor.JavaLevelExplorer", "edit", None
                    ),
                    lambda: self._edit_item(path_item),
                )

            menu.exec(self.mapToGlobal(point))
            menu.deleteLater()

    @staticmethod
    def _open_in_explorer(item: QTreeWidgetItem) -> None:
        if not isinstance(item, PathItem):
            return
        path = os.path.dirname(item.path)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def _edit_item(self, item: QTreeWidgetItem) -> None:
        if not isinstance(item, PathItem):
            return
        if os.path.isfile(item.path) and item.path.endswith((".dat", ".dat_old")):
            with CatchExceptionDialog(f"Error editing {item.path}"):
                named_tag = read_nbt(item.path, preset=java_encoding)
                dialog = NBTDialog(named_tag)
                if dialog.exec():
                    tag = dialog.get_tag()
                    if Path(self._level.path) / "level.dat" == Path(item.path):
                        if isinstance(tag, NamedTag):
                            self._level.raw_level.level_dat = tag
                    else:
                        tmp_path = item.path + "atmp"
                        tag.save_to(tmp_path, preset=java_encoding)
                        os.replace(tmp_path, item.path)

    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        super().mouseDoubleClickEvent(event)
        self.mousePressEvent(event)
