import os

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QMenu,
    QApplication,
)

from amulet.nbt import (
    read_snbt,
    NamedTag,
    ByteTag,
    ShortTag,
    IntTag,
    LongTag,
    FloatTag,
    DoubleTag,
    ByteArrayTag,
    StringTag,
    ListTag,
    CompoundTag,
    IntArrayTag,
    LongArrayTag,
)

from amulet.app.exception import CatchExceptionDialog

from ._spin import NBTSpinBox

type TagType = (
    NamedTag
    | ByteTag
    | ShortTag
    | IntTag
    | LongTag
    | FloatTag
    | DoubleTag
    | ByteArrayTag
    | StringTag
    | ListTag
    | CompoundTag
    | IntArrayTag
    | LongArrayTag
)


_icons: dict[type[TagType], QPixmap] = {}


def get_icon(tag_cls: type[TagType]) -> QPixmap | None:
    if not _icons:
        icon_sheet = QPixmap(
            os.path.realpath(os.path.join(os.path.dirname(__file__), "nbtsheet.png"))
        )
        for x, y, cls in [
            (0, 0, ByteTag),
            (1, 0, DoubleTag),
            (2, 0, FloatTag),
            (3, 0, IntTag),
            (0, 1, LongTag),
            (1, 1, ShortTag),
            (2, 1, StringTag),
            (3, 1, CompoundTag),
            (0, 2, ByteArrayTag),
            (1, 2, IntArrayTag),
            (2, 2, ListTag),
            (3, 2, LongArrayTag),
        ]:
            _icons[cls] = icon_sheet.copy(32 * x, 32 * y, 32, 32)
    return _icons.get(tag_cls)


def _get_tag_str(tag: TagType) -> str:
    if isinstance(
        tag,
        (
            ByteTag,
            ShortTag,
            IntTag,
            LongTag,
            FloatTag,
            DoubleTag,
        ),
    ):
        return tag.to_snbt()
    elif isinstance(tag, ByteArrayTag):
        return f"[B;{QApplication.translate("plugin.amulet.nbt", "count_items", None).format(count=len(tag))}]"
    elif isinstance(tag, IntArrayTag):
        return f"[I;{QApplication.translate("plugin.amulet.nbt", "count_items", None).format(count=len(tag))}]"
    elif isinstance(tag, LongArrayTag):
        return f"[L;{QApplication.translate("plugin.amulet.nbt", "count_items", None).format(count=len(tag))}]"
    elif isinstance(tag, StringTag):
        return repr(tag.py_str_or_bytes)
    elif isinstance(tag, ListTag):
        if tag:
            return f"[{QApplication.translate("plugin.amulet.nbt", "count_items", None).format(count=len(tag))}]"
        else:
            return "[]"
    elif isinstance(tag, CompoundTag):
        if tag:
            return f"{{{QApplication.translate("plugin.amulet.nbt", "count_items", None).format(count=len(tag))}}}"
        return "{}"
    elif isinstance(tag, NamedTag):
        return f"NamedTag({_get_tag_str(tag.tag)}, {tag.name!r})"
    else:
        raise TypeError(f"Unknown tag type {type(tag)}")


class NBTTreeWidgetItem(QTreeWidgetItem):
    def __init__(
        self,
        parent: QTreeWidgetItem | None,
        tag: TagType,
        key: str | bytes | None = None,
    ) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self._expanded = False
        self._tag = tag
        self._key = key
        self._set_text()
        self._set_icon()
        self._set_child_policy()

    def __del__(self) -> None:
        print("del NBTTreeWidgetItem")

    def get_tag(self) -> TagType:
        return self._tag

    def set_tag(self, tag: TagType) -> None:
        """Set the tag for this item."""
        parent = self.parent()
        if isinstance(parent, NBTTreeWidgetItem):
            parent_tag = parent.get_tag()
            if isinstance(tag, NamedTag):
                raise TypeError("NamedTag cannot be a child of another tag")
            if isinstance(parent_tag, CompoundTag):
                if self._key is None:
                    raise RuntimeError("Item with CompoundTag parent has no key")
                parent_tag[self._key] = tag
            elif isinstance(parent_tag, ListTag):
                parent_tag[parent.indexOfChild(self)] = tag
            elif isinstance(parent_tag, NamedTag):
                parent_tag.tag = tag
            elif isinstance(parent_tag, ByteArrayTag):
                if not isinstance(tag, ByteTag):
                    raise TypeError("ByteArrayTag can only contain ByteTag")
                parent_tag[parent.indexOfChild(self)] = tag
            elif isinstance(parent_tag, IntArrayTag):
                if not isinstance(tag, IntTag):
                    raise TypeError("IntArrayTag can only contain IntTag")
                parent_tag[parent.indexOfChild(self)] = tag
            elif isinstance(parent_tag, LongArrayTag):
                if not isinstance(tag, LongTag):
                    raise TypeError("LongArrayTag can only contain LongTag")
                parent_tag[parent.indexOfChild(self)] = tag
            else:
                raise RuntimeError(f"Unsupported parent type {type(parent_tag)}")
        self._tag = tag
        self._set_text()
        self._set_icon()
        self._remove_children()
        self._set_child_policy()

    def get_key(self) -> str | bytes | None:
        return self._key

    def _set_text(self) -> None:
        """Set the text for this item."""
        self.setText(
            0, (f"{self._key!r}: " if self._key else "") + _get_tag_str(self._tag)
        )

    def _set_icon(self) -> None:
        """Set the icon for this item."""
        icon = get_icon(type(self._tag))
        self.setIcon(0, icon or QPixmap())

    def _set_child_policy(self) -> None:
        if isinstance(self._tag, NamedTag) or (
            isinstance(
                self._tag,
                (ListTag, CompoundTag, ByteArrayTag, IntArrayTag, LongArrayTag),
            )
            and self._tag
        ):
            self.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )
        else:
            self.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicatorWhenChildless
            )

    def _remove_children(self) -> None:
        """Remove all children of this item."""
        while self.childCount():
            self.takeChild(0)

    def populate_children(self) -> None:
        """Populate the children of this item."""
        if self._expanded:
            return
        self._expanded = True
        tag = self._tag
        if isinstance(tag, NamedTag):
            NBTTreeWidgetItem(self, tag.tag)
        elif isinstance(tag, ListTag):
            for item in tag:
                NBTTreeWidgetItem(self, item)
        elif isinstance(tag, CompoundTag):
            for key, item in sorted(tag.items(), key=lambda v: v[0]):
                NBTTreeWidgetItem(self, item, key)
        elif isinstance(tag, ByteArrayTag):
            for item in tag:
                NBTTreeWidgetItem(self, ByteTag(item))
        elif isinstance(tag, IntArrayTag):
            for item in tag:
                NBTTreeWidgetItem(self, IntTag(item))
        elif isinstance(tag, LongArrayTag):
            for item in tag:
                NBTTreeWidgetItem(self, LongTag(item))

    def copy_snbt(self) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "copy_fail", None)
        ):
            clipboard = QApplication.clipboard()
            clipboard.setText(self._tag.to_snbt())

    def paste_snbt(self) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "paste_fail", None)
        ):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            nbt = read_snbt(text)
            self.set_tag(nbt)


class EditDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        widget: QWidget,
        title: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(widget)
        self._buttons = QDialogButtonBox(self)
        self._buttons.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._layout.addWidget(self._buttons)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)


class NBTTreeWidget(QTreeWidget):
    def __init__(self, tag: TagType) -> None:
        super().__init__()

        self.setColumnCount(1)
        self.setHeaderHidden(True)

        self.itemExpanded.connect(self._item_expanded)
        self.set_tag(tag)

        self.itemDoubleClicked.connect(self._double_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._right_clicked)

    def get_tag(self) -> TagType:
        item = self.topLevelItem(0)
        if not isinstance(item, NBTTreeWidgetItem):
            raise RuntimeError
        return item.get_tag()

    def set_tag(self, tag: TagType) -> None:
        self.clear()
        item = NBTTreeWidgetItem(None, tag)
        self.insertTopLevelItem(0, item)
        item.setExpanded(True)
        if isinstance(tag, NamedTag):
            for i in range(item.childCount()):
                item.child(i).setExpanded(True)

    def _edit_item(self, item: NBTTreeWidgetItem) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "edit_fail", None)
        ):
            tag = item.get_tag()
            if isinstance(
                tag, (ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag)
            ):
                spin_widget = NBTSpinBox(tag)
                dialog = EditDialog(
                    self,
                    spin_widget,
                    QApplication.translate(
                        "plugin.amulet.nbt", "edit_tag", None
                    ).format(cls=type(tag).__name__),
                )
                if dialog.exec():
                    item.set_tag(spin_widget.value())
            elif isinstance(tag, StringTag):
                str_widget = QLineEdit(tag.py_str)
                dialog = EditDialog(
                    self,
                    str_widget,
                    QApplication.translate(
                        "plugin.amulet.nbt", "edit_tag", None
                    ).format(cls="StringTag"),
                )
                if dialog.exec():
                    item.set_tag(StringTag(str_widget.text()))

    def _double_clicked(self, item: QTreeWidgetItem) -> None:
        if isinstance(item, NBTTreeWidgetItem):
            self._edit_item(item)

    @staticmethod
    def _item_expanded(item: QTreeWidgetItem) -> None:
        if isinstance(item, NBTTreeWidgetItem):
            item.populate_children()

    def _right_clicked(self, point: QPoint) -> None:
        item = self.itemAt(point)
        if isinstance(item, NBTTreeWidgetItem):
            nbt_item = item
            menu = QMenu(self)
            menu.addAction(
                QApplication.translate("plugin.amulet.nbt", "edit", None),
                lambda: self._edit_item(nbt_item),
            )
            menu.addAction(
                QApplication.translate("plugin.amulet.nbt", "copy", None),
                lambda: nbt_item.copy_snbt(),
            )
            menu.addAction(
                QApplication.translate("plugin.amulet.nbt", "paste", None),
                lambda: nbt_item.paste_snbt(),
            )
            menu.exec(self.mapToGlobal(point))


class NBTWidget(QWidget):
    def __init__(self, tag: TagType | None = None) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._tree_widget = NBTTreeWidget(NamedTag() if tag is None else tag)
        self._layout.addWidget(self._tree_widget)

    def get_tag(self) -> TagType:
        return self._tree_widget.get_tag()

    def set_tag(self, tag: TagType) -> None:
        self._tree_widget.set_tag(tag)
