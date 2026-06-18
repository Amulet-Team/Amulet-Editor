from copy import deepcopy
from typing import SupportsInt, Literal, overload

from PySide6.QtCore import QPoint, Qt, QSize, QEvent, QTimer
from PySide6.QtGui import QPixmap, QKeyEvent, QMouseEvent, QEnterEvent, QIcon
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
    QHBoxLayout,
    QPushButton,
    QToolTip,
    QMessageBox,
    QLayout,
    QComboBox,
)
from PySide6.QtSvgWidgets import QSvgWidget

from amulet.nbt import (
    read_snbt,
    NamedTag,
    AnyNBT,
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
    utf8_escape_encoding,
)

from amulet.app.exception import CatchExceptionDialog

from plugin.tablericons import tablericons

from ._spin import NBTSpinBox
from ..icon import get_pixmap, get_icon

type TagType = NamedTag | AnyNBT


def get_string(v: str | bytes) -> str:
    """Convert an NBT key or string to a Python string."""
    if isinstance(v, str):
        return v
    return utf8_escape_encoding.decode(v).decode("utf-8")


def items_str(count: int) -> str:
    """Get the translation string for the number of items."""
    if count == 1:
        return QApplication.translate("plugin.amulet.nbt", "count_items", None)
    return QApplication.translate("plugin.amulet.nbt", "count_items_single", None)


def _get_tag_str(tag: TagType) -> str:
    """Get the string representation of a tag."""
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
        return f"[B;{items_str(len(tag)).format(count=len(tag))}]"
    elif isinstance(tag, IntArrayTag):
        return f"[I;{items_str(len(tag)).format(count=len(tag))}]"
    elif isinstance(tag, LongArrayTag):
        return f"[L;{items_str(len(tag)).format(count=len(tag))}]"
    elif isinstance(tag, StringTag):
        return repr(get_string(tag.py_str_or_bytes))
    elif isinstance(tag, ListTag):
        if tag:
            return f"[{items_str(len(tag)).format(count=len(tag))}]"
        else:
            return "[]"
    elif isinstance(tag, CompoundTag):
        if tag:
            return f"{{{items_str(len(tag)).format(count=len(tag))}}}"
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

        self._children_populated = False
        self._tag = tag
        self._key = key
        self.update_text()
        self.update_icon()
        self._set_child_policy()

    def get_tag(self) -> TagType:
        return self._tag

    def set_tag(self, tag: TagType, update_parent: bool) -> None:
        if update_parent:
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

    def set_tag_and_display(self, tag: TagType, update_parent: bool) -> None:
        """Set the tag and update the display."""
        self.set_tag(tag, update_parent)
        self.update_text()
        self.update_icon()
        self._remove_children()
        self._set_child_policy()

    def get_key(self) -> str | bytes | None:
        return self._key

    def set_key(self, key: str | bytes) -> None:
        """Set the key for this item."""
        if isinstance(self._tag, NamedTag):
            self._tag.name = key
        elif self._key is not None:
            self._key = key
        else:
            raise RuntimeError(
                "Key can only be set for NamedTag or child of CompoundTag"
            )
        self.update_text()

    def update_text(self) -> None:
        """Set the text for this item."""
        text = _get_tag_str(self._tag)
        parent_item = self.parent()
        if isinstance(parent_item, NBTTreeWidgetItem):
            parent_tag = parent_item.get_tag()
            if isinstance(
                parent_tag, (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag)
            ):
                text = f"{parent_item.indexOfChild(self)}: " + text
        if self._key is not None:
            text = f"{self._key or ""!r}: {text}"
        self.setText(0, text)

    def update_icon(self) -> None:
        """Set the icon for this item."""
        icon = get_pixmap(type(self._tag))
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
        """Collapse and remove this item's children."""
        self.setExpanded(False)
        while self.childCount():
            self.takeChild(0)
        self._children_populated = False

    def populate_children(self) -> None:
        """Populate this item's children."""
        if self._children_populated:
            return
        self._children_populated = True
        while self.childCount():
            self.takeChild(0)
        tag = self._tag
        if isinstance(tag, NamedTag):
            NBTTreeWidgetItem(self, tag.tag)
        elif isinstance(tag, ListTag):
            for item in tag:
                NBTTreeWidgetItem(self, item)
        elif isinstance(tag, CompoundTag):
            for key, item in sorted(
                tag.items(), key=lambda v: (isinstance(v[0], bytes), v[0])
            ):
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


class EditDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        child: QWidget | QLayout,
        title: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._layout = QVBoxLayout(self)
        if isinstance(child, QWidget):
            self._layout.addWidget(child)
        elif isinstance(child, QLayout):
            self._layout.addLayout(child)
        self._buttons = QDialogButtonBox(self)
        self._buttons.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._layout.addWidget(self._buttons)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)


def edit_numeric_tag[
    TagT: ByteTag | ShortTag | IntTag | LongTag | FloatTag | DoubleTag
](
    parent: QWidget, tag: TagT, title: str
) -> TagT | None:
    widget = NBTSpinBox(tag)
    dialog = EditDialog(
        parent,
        widget,
        title,
    )
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return widget.value()
    return None


def edit_string_tag(parent: QWidget, tag: StringTag, title: str) -> StringTag | None:
    text = tag.py_str_or_bytes
    if isinstance(text, bytes):
        text = get_string(text)
    widget = QLineEdit(text)
    dialog = EditDialog(
        parent,
        widget,
        title,
    )
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return StringTag(widget.text())
    return None


@overload
def edit_tag(
    parent: QWidget, tag: AnyNBT, title: str, named: Literal[True]
) -> NamedTag | None: ...
@overload
def edit_tag(
    parent: QWidget, tag: AnyNBT, title: str, named: Literal[False]
) -> AnyNBT | None: ...
def edit_tag(
    parent: QWidget, tag: AnyNBT, title: str, named: bool
) -> AnyNBT | NamedTag | None:
    layout = QVBoxLayout()

    if named:
        name_entry = QLineEdit(
            placeholderText=QApplication.translate(
                "plugin.amulet.nbt", "name_placeholder", None
            )
        )
        layout.addWidget(name_entry)
    else:
        name_entry = None

    tag_choice = QComboBox()
    layout.addWidget(tag_choice)
    tag_choice.addItem(get_icon(ByteTag) or QIcon(), "ByteTag")
    tag_choice.addItem(get_icon(ShortTag) or QIcon(), "ShortTag")
    tag_choice.addItem(get_icon(IntTag) or QIcon(), "IntTag")
    tag_choice.addItem(get_icon(LongTag) or QIcon(), "LongTag")
    tag_choice.addItem(get_icon(FloatTag) or QIcon(), "FloatTag")
    tag_choice.addItem(get_icon(DoubleTag) or QIcon(), "DoubleTag")
    tag_choice.addItem(get_icon(StringTag) or QIcon(), "StringTag")
    tag_choice.addItem(get_icon(ListTag) or QIcon(), "ListTag")
    tag_choice.addItem(get_icon(CompoundTag) or QIcon(), "CompoundTag")
    tag_choice.addItem(get_icon(ByteArrayTag) or QIcon(), "ByteArrayTag")
    tag_choice.addItem(get_icon(IntArrayTag) or QIcon(), "IntArrayTag")
    tag_choice.addItem(get_icon(LongArrayTag) or QIcon(), "LongArrayTag")

    tag_id = tag.tag_id
    if tag_id <= 6 or 11 <= tag_id <= 12:
        tag_choice.setCurrentIndex(tag_id - 1)
    elif tag_id == 7:
        tag_choice.setCurrentIndex(9)
    elif 8 <= tag_id <= 10:
        tag_choice.setCurrentIndex(tag_id - 2)
    else:
        raise RuntimeError(f"Unknown tag id: {tag_id}")

    dialog = EditDialog(
        parent,
        layout,
        title,
    )

    widget: (
        NBTSpinBox[ByteTag | ShortTag | IntTag | LongTag | FloatTag | DoubleTag]
        | QLineEdit
        | None
    ) = None

    def set_widget(widget_: NBTSpinBox | QLineEdit | None) -> None:
        nonlocal widget
        if widget is not None:
            layout.removeWidget(widget)
            widget.hide()
            widget.deleteLater()
            widget = None
        if widget_ is not None:
            layout.addWidget(widget_)
            QTimer.singleShot(0, lambda: widget_.setFixedHeight(tag_choice.height()))
            widget = widget_
        QTimer.singleShot(0, dialog.adjustSize)

    if isinstance(tag, (ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag)):
        set_widget(NBTSpinBox(tag))
    elif isinstance(tag, StringTag):
        text = tag.py_str_or_bytes
        if isinstance(text, bytes):
            text = get_string(text)
        set_widget(QLineEdit(text))

    def cls_changed(i: int) -> None:
        if i <= 5:
            set_widget(
                NBTSpinBox(
                    [ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag][i]()
                )
            )
        elif i == 6:
            set_widget(QLineEdit())
        else:
            set_widget(None)

    tag_choice.currentIndexChanged.connect(cls_changed)

    if dialog.exec() == QDialog.DialogCode.Accepted:

        def get_tag() -> AnyNBT:
            if isinstance(widget, NBTSpinBox):
                return widget.value()
            elif isinstance(widget, QLineEdit):
                return StringTag(widget.text())
            else:
                index = tag_choice.currentIndex()
                if index == 7:
                    return ListTag()
                elif index == 8:
                    return CompoundTag()
                elif index == 9:
                    return ByteArrayTag()
                elif index == 10:
                    return IntArrayTag()
                elif index == 11:
                    return LongArrayTag()
            raise RuntimeError

        if isinstance(name_entry, QLineEdit):
            return NamedTag(get_tag(), name_entry.text())
        else:
            return get_tag()
    return None


class SVGButton(QPushButton):
    """A QPushButton containing a stylable icon."""

    def __init__(self, icon_path: str) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon = QSvgWidget(icon_path)
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._layout.addWidget(self._icon)
        self._tip: str = ""

    def setToolTip(self, tip: str) -> None:
        self._tip = tip

    def toolTip(self) -> str:
        return self._tip

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        if self._tip:
            pos = self.mapToGlobal(self.rect().bottomLeft())
            # QToolTip adds an offset that we have to subtract.
            pos.setY(pos.y() - int(16 / self.devicePixelRatio()))
            QToolTip.showText(pos, self._tip, self)


class TreeWidget(QTreeWidget):
    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        super().mouseDoubleClickEvent(event)
        self.mousePressEvent(event)


class NBTWidgetP(QWidget):
    def __init__(self, tag: TagType) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._tool_layout = QHBoxLayout()
        self._layout.addLayout(self._tool_layout)

        self._rename_button = SVGButton(tablericons.outline.cursor_text)
        self._rename_button.setFixedSize(QSize(30, 30))
        self._rename_button.clicked.connect(self._rename_current_item)
        self._tool_layout.addWidget(self._rename_button)

        self._edit_tag_button = SVGButton(tablericons.outline.pencil)
        self._edit_tag_button.setFixedSize(QSize(30, 30))
        self._edit_tag_button.clicked.connect(self._edit_current_item_tag)
        self._tool_layout.addWidget(self._edit_tag_button)

        self._add_button = SVGButton(tablericons.outline.plus)
        self._add_button.setFixedSize(QSize(30, 30))
        self._add_button.clicked.connect(self._add_current_item)
        self._tool_layout.addWidget(self._add_button)

        self._duplicate_button = SVGButton(tablericons.outline.copy_plus)
        self._duplicate_button.setFixedSize(QSize(30, 30))
        self._duplicate_button.clicked.connect(self._duplicate_current_item)
        self._tool_layout.addWidget(self._duplicate_button)

        self._delete_button = SVGButton(tablericons.outline.trash)
        self._delete_button.setFixedSize(QSize(30, 30))
        self._delete_button.clicked.connect(self._delete_current_item)
        self._tool_layout.addWidget(self._delete_button)

        self._cut_button = SVGButton(tablericons.outline.scissors)
        self._cut_button.setFixedSize(QSize(30, 30))
        self._cut_button.clicked.connect(self._cut_current_item)
        self._tool_layout.addWidget(self._cut_button)

        self._copy_button = SVGButton(tablericons.outline.copy)
        self._copy_button.setFixedSize(QSize(30, 30))
        self._copy_button.clicked.connect(self._copy_current_item)
        self._tool_layout.addWidget(self._copy_button)

        self._paste_button = SVGButton(tablericons.outline.clipboard)
        self._paste_button.setFixedSize(QSize(30, 30))
        self._paste_button.clicked.connect(self._paste_current_item)
        self._tool_layout.addWidget(self._paste_button)

        self._move_up_button = SVGButton(tablericons.outline.arrow_up)
        self._move_up_button.setFixedSize(QSize(30, 30))
        self._move_up_button.clicked.connect(self._move_current_item_up)
        self._tool_layout.addWidget(self._move_up_button)

        self._move_down_button = SVGButton(tablericons.outline.arrow_down)
        self._move_down_button.setFixedSize(QSize(30, 30))
        self._move_down_button.clicked.connect(self._move_current_item_down)
        self._tool_layout.addWidget(self._move_down_button)

        self._tool_layout.addStretch(1)

        self._tree = TreeWidget(self)
        self._layout.addWidget(self._tree)

        self._tree.setColumnCount(1)
        self._tree.setHeaderHidden(True)
        self._tree.setExpandsOnDoubleClick(False)

        self._localise()

        self._tree.itemExpanded.connect(self._populate_children)
        self._tree.currentItemChanged.connect(self._update_buttons)
        self.set_tag(tag)

        self._tree.itemDoubleClicked.connect(self._double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._right_clicked)

    def _update_buttons(self, item: QTreeWidgetItem | None = None) -> None:
        if item is None:
            item = self._tree.currentItem()
        if not isinstance(item, NBTTreeWidgetItem):
            return
        self._rename_button.setEnabled(self._supports_rename(item))
        self._edit_tag_button.setEnabled(self._supports_edit_tag(item))
        self._add_button.setEnabled(self._supports_add_item(item))
        self._duplicate_button.setEnabled(self._supports_duplicate(item))
        self._delete_button.setEnabled(self._supports_delete(item))
        self._cut_button.setEnabled(self._supports_cut(item))
        # TODO: paste
        self._move_up_button.setEnabled(self._supports_move_up(item))
        self._move_down_button.setEnabled(self._supports_move_down(item))

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        def localise_item(item: QTreeWidgetItem | None) -> None:
            if isinstance(item, NBTTreeWidgetItem):
                item.update_text()
                for i2 in range(item.childCount()):
                    localise_item(item.child(i2))

        for i in range(self._tree.topLevelItemCount()):
            localise_item(self._tree.topLevelItem(i))

        self._rename_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "rename_tooltip", None)
        )
        self._edit_tag_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "edit_tag_tooltip", None)
        )
        self._add_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "add_tooltip", None)
        )
        self._duplicate_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "duplicate_tooltip", None)
        )
        self._delete_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "delete_tooltip", None)
        )
        self._cut_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "cut_tooltip", None)
        )
        self._copy_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "copy_tooltip", None)
        )
        self._paste_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "paste_tooltip", None)
        )
        self._move_up_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "move_up_tooltip", None)
        )
        self._move_down_button.setToolTip(
            QApplication.translate("plugin.amulet.nbt", "move_down_tooltip", None)
        )
        # TODO: localise buttons

    def get_tag(self) -> TagType:
        item = self._tree.topLevelItem(0)
        if not isinstance(item, NBTTreeWidgetItem):
            raise RuntimeError
        return item.get_tag()

    def set_tag(self, tag: TagType) -> None:
        self._tree.clear()
        item = NBTTreeWidgetItem(None, tag)
        self._tree.insertTopLevelItem(0, item)
        item.setExpanded(True)
        if isinstance(tag, NamedTag):
            for i in range(item.childCount()):
                child = item.child(i)
                if child is not None:
                    child.setExpanded(True)
        self._tree.setCurrentItem(item)

    @staticmethod
    def _populate_children(item: QTreeWidgetItem) -> None:
        if isinstance(item, NBTTreeWidgetItem):
            item.populate_children()

    def _double_clicked(self, item: QTreeWidgetItem) -> None:
        if isinstance(item, NBTTreeWidgetItem):
            self._edit_item_tag(item)

    def _right_clicked(self, point: QPoint) -> None:
        item = self._tree.itemAt(point)
        if isinstance(item, NBTTreeWidgetItem):
            menu = QMenu(self)
            if self._supports_rename(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "rename", None),
                    self._rename_current_item,
                )
            if self._supports_edit_tag(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "edit_tag", None),
                    self._edit_current_item_tag,
                )
            if self._supports_add_item(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "add", None),
                    self._add_current_item,
                )
            if self._supports_duplicate(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "duplicate", None),
                    self._duplicate_current_item,
                )
            if self._supports_delete(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "delete", None),
                    self._delete_current_item,
                )
            if self._supports_cut(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "cut", None),
                    self._cut_current_item,
                )
            menu.addAction(
                QApplication.translate("plugin.amulet.nbt", "copy", None),
                self._copy_current_item,
            )
            menu.addAction(
                QApplication.translate("plugin.amulet.nbt", "paste", None),
                self._paste_current_item,
            )
            # menu.addAction(
            #     QApplication.translate("plugin.amulet.nbt", "paste_insert", None),
            #     lambda: None,
            # )
            # menu.addAction(
            #     QApplication.translate("plugin.amulet.nbt", "paste_prepend", None),
            #     lambda: None,
            # )
            if self._supports_move_up(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "move_up", None),
                    self._move_current_item_up,
                )
            if self._supports_move_down(item):
                menu.addAction(
                    QApplication.translate("plugin.amulet.nbt", "move_down", None),
                    self._move_current_item_down,
                )
            menu.exec(self._tree.mapToGlobal(point))
            menu.deleteLater()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            item = self._tree.currentItem()
            if isinstance(item, NBTTreeWidgetItem):
                self._delete_item(item)
        elif (
            event.key() == Qt.Key.Key_C
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            item = self._tree.currentItem()
            if isinstance(item, NBTTreeWidgetItem):
                item.copy_snbt()
        elif (
            event.key() == Qt.Key.Key_X
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            item = self._tree.currentItem()
            if isinstance(item, NBTTreeWidgetItem):
                self._cut_item(item)
        elif (
            event.key() == Qt.Key.Key_V
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            item = self._tree.currentItem()
            if isinstance(item, NBTTreeWidgetItem):
                self._paste_item(item)
        else:
            super().keyPressEvent(event)

    def _set_compound_tag(
        self,
        compound_tag: CompoundTag,
        compound_item: NBTTreeWidgetItem,
        new_key: str | bytes,
        new_tag: AnyNBT,
        replace: tuple[str | bytes, NBTTreeWidgetItem] | None = None,
    ) -> None:
        if new_key in compound_tag:
            # Check that the user wants to overwrite the other value
            message_box = QMessageBox()
            message_box.setText(
                QApplication.translate("plugin.amulet.nbt", "replace_tag_confirm", None)
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if message_box.exec() == QMessageBox.StandardButton.No:
                return
            compound_item.setExpanded(True)
            if replace is None:
                size_changed = False
            else:
                size_changed = True
                compound_item.removeChild(replace[1])
            # Find the other item and set its tag
            for i in range(compound_item.childCount()):
                child = compound_item.child(i)
                if isinstance(child, NBTTreeWidgetItem) and child.get_key() == new_key:
                    child.set_tag_and_display(new_tag, False)
                    self._tree.setCurrentItem(child)
                    break
            else:
                raise RuntimeError("Could not find item to replace")
        else:
            compound_item.setExpanded(True)
            if replace is None:
                size_changed = True
                item = NBTTreeWidgetItem(None, new_tag, new_key)
            else:
                size_changed = False
                item = replace[1]
                compound_item.removeChild(item)
                item.set_key(new_key)
            for i in range(compound_item.childCount()):
                child = compound_item.child(i)
                if not isinstance(child, NBTTreeWidgetItem):
                    continue
                child_key = child.get_key()
                if child_key is None:
                    continue
                if (False, new_key) < (
                    isinstance(child_key, bytes),
                    child_key,
                ):
                    compound_item.insertChild(i, item)
                    break
            else:
                compound_item.addChild(item)
            self._tree.setCurrentItem(item)
        if replace is not None:
            compound_tag.pop(replace[0], None)
        compound_tag[new_key] = new_tag
        if size_changed:
            compound_item.update_text()

    @staticmethod
    def _supports_rename(item: NBTTreeWidgetItem) -> bool:
        if isinstance(item.get_tag(), NamedTag):
            return True
        parent_item = item.parent()
        if isinstance(parent_item, NBTTreeWidgetItem):
            return isinstance(parent_item.get_tag(), CompoundTag)
        return False

    def _rename_item(self, item: NBTTreeWidgetItem) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "edit_fail", None)
        ):
            tag = item.get_tag()
            if isinstance(tag, NamedTag):
                name = tag.name
                if isinstance(name, bytes):
                    name = get_string(name)
                str_widget = QLineEdit(name)
                dialog = EditDialog(
                    self,
                    str_widget,
                    QApplication.translate(
                        "plugin.amulet.nbt", "edit_tag_cls", None
                    ).format(cls="NamedTag"),
                )
                if dialog.exec():
                    item.set_key(str_widget.text())
            else:
                parent_item = item.parent()
                if not isinstance(parent_item, NBTTreeWidgetItem):
                    return
                parent_tag = parent_item.get_tag()
                if isinstance(parent_tag, CompoundTag):
                    key = item.get_key()
                    if key is None:
                        return
                    key_str = get_string(key)
                    str_widget = QLineEdit(key_str)
                    dialog = EditDialog(
                        self,
                        str_widget,
                        QApplication.translate("plugin.amulet.nbt", "rename", None),
                    )
                    if dialog.exec():
                        new_key = str_widget.text()
                        if new_key != key_str:
                            self._set_compound_tag(
                                parent_tag,
                                parent_item,
                                new_key,
                                tag,
                                (key, item),
                            )

    def _rename_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._rename_item(item)

    @staticmethod
    def _supports_edit_tag(item: NBTTreeWidgetItem) -> bool:
        return isinstance(
            item.get_tag(),
            (
                ByteTag,
                ShortTag,
                IntTag,
                LongTag,
                FloatTag,
                DoubleTag,
                StringTag,
            ),
        )

    def _edit_item_tag(self, item: NBTTreeWidgetItem) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "edit_fail", None)
        ):
            tag = item.get_tag()
            new_tag: AnyNBT | None
            if isinstance(
                tag, (ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag)
            ):
                new_tag = edit_numeric_tag(
                    self,
                    tag,
                    QApplication.translate(
                        "plugin.amulet.nbt", "edit_tag_cls", None
                    ).format(cls=type(tag).__name__),
                )

            elif isinstance(tag, StringTag):
                new_tag = edit_string_tag(
                    self,
                    tag,
                    QApplication.translate(
                        "plugin.amulet.nbt", "edit_tag_cls", None
                    ).format(cls="StringTag"),
                )
            else:
                new_tag = None

            if new_tag is not None:
                item.set_tag_and_display(new_tag, True)

    def _edit_current_item_tag(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._edit_item_tag(item)

    def _supports_cut(self, item: NBTTreeWidgetItem) -> bool:
        return self._supports_delete(item)

    def _cut_item(self, item: NBTTreeWidgetItem) -> None:
        item.copy_snbt()
        self._delete_item(item)

    def _cut_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._cut_item(item)

    def _copy_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            item.copy_snbt()

    @staticmethod
    def _paste_item(item: NBTTreeWidgetItem) -> None:
        with CatchExceptionDialog(
            QApplication.translate("plugin.amulet.nbt", "paste_fail", None)
        ):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            nbt = read_snbt(text)
            item.set_tag_and_display(nbt, True)

    def _paste_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._paste_item(item)

    @staticmethod
    def _supports_add_item(item: NBTTreeWidgetItem) -> bool:
        return isinstance(
            item.get_tag(),
            (ListTag, CompoundTag, ByteArrayTag, IntArrayTag, LongArrayTag),
        )

    def _add_item(self, item: NBTTreeWidgetItem) -> None:
        tag = item.get_tag()
        if isinstance(tag, ListTag):
            new_tag: AnyNBT | None
            if tag:
                element_cls = tag.element_class
                if element_cls is None:
                    return
                new_tag = element_cls()
                if isinstance(
                    new_tag, (ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag)
                ):
                    new_tag = edit_numeric_tag(
                        self,
                        new_tag,
                        QApplication.translate(
                            "plugin.amulet.nbt", "edit_tag_cls", None
                        ).format(cls=type(new_tag).__name__),
                    )
            else:
                new_tag = edit_tag(
                    self,
                    ByteTag(),
                    QApplication.translate("plugin.amulet.nbt", "add", None),
                    False,
                )
            if new_tag is not None:
                tag.append(new_tag)
                item.update_text()
                NBTTreeWidgetItem(item, new_tag)
        elif isinstance(tag, CompoundTag):
            new_named_tag = edit_tag(
                self,
                ByteTag(),
                QApplication.translate("plugin.amulet.nbt", "add", None),
                True,
            )
            if new_named_tag is not None:
                new_key = new_named_tag.name
                new_tag = new_named_tag.tag
                self._set_compound_tag(tag, item, new_key, new_tag)
        else:
            arr_cls: type[ByteArrayTag | IntArrayTag | LongArrayTag]
            new_arr_tag: ByteTag | IntTag | LongTag | None
            if isinstance(tag, ByteArrayTag):
                arr_cls = ByteArrayTag
                new_arr_tag = ByteTag()
                cls_name = "ByteTag"
            elif isinstance(tag, IntArrayTag):
                arr_cls = IntArrayTag
                new_arr_tag = IntTag()
                cls_name = "IntTag"
            elif isinstance(tag, LongArrayTag):
                arr_cls = LongArrayTag
                new_arr_tag = LongTag()
                cls_name = "LongTag"
            else:
                return
            new_arr_tag = edit_numeric_tag(
                self,
                new_arr_tag,
                QApplication.translate(
                    "plugin.amulet.nbt", "edit_tag_cls", None
                ).format(cls=cls_name),
            )
            if new_arr_tag is not None:
                l: list[SupportsInt] = list(tag)
                l.append(new_arr_tag)
                item.set_tag(arr_cls(l), True)
                item.update_text()
                NBTTreeWidgetItem(item, new_arr_tag)

    def _add_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._add_item(item)

    def _supports_duplicate(self, item: NBTTreeWidgetItem) -> bool:
        if item is None:
            item = self._tree.currentItem()
            if not isinstance(item, NBTTreeWidgetItem):
                return False
        parent = item.parent()
        return isinstance(parent, NBTTreeWidgetItem) and isinstance(
            parent.get_tag(), (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag)
        )

    @staticmethod
    def _duplicate_item(item: NBTTreeWidgetItem) -> None:
        parent_item = item.parent()
        if not isinstance(parent_item, NBTTreeWidgetItem):
            return
        i = parent_item.indexOfChild(item)
        parent_tag = parent_item.get_tag()
        if isinstance(parent_tag, ListTag):
            new_tag = deepcopy(item.get_tag())
            parent_tag.insert(i, new_tag)
        elif isinstance(parent_tag, ByteArrayTag):
            arr: list[SupportsInt] = list(parent_tag)
            arr.insert(i, arr[i])
            new_tag = ByteTag(arr[i])
            parent_item.set_tag(ByteArrayTag(arr), True)
            parent_item.update_text()
        elif isinstance(parent_tag, IntArrayTag):
            arr = list(parent_tag)
            arr.insert(i, arr[i])
            new_tag = IntTag(arr[i])
            parent_item.set_tag(IntArrayTag(arr), True)
            parent_item.update_text()
        elif isinstance(parent_tag, LongArrayTag):
            arr = list(parent_tag)
            arr.insert(i, arr[i])
            new_tag = LongTag(arr[i])
            parent_item.set_tag(LongArrayTag(arr), True)
            parent_item.update_text()
        else:
            return
        new_item = NBTTreeWidgetItem(None, new_tag)
        parent_item.insertChild(i, new_item)
        for i2 in range(i, parent_item.childCount()):
            child = parent_item.child(i2)
            if isinstance(child, NBTTreeWidgetItem):
                child.update_text()

    def _duplicate_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._duplicate_item(item)

    @staticmethod
    def _supports_delete(item: NBTTreeWidgetItem) -> bool:
        parent_item = item.parent()
        return isinstance(parent_item, NBTTreeWidgetItem) and isinstance(
            parent_item.get_tag(),
            (CompoundTag, ListTag, ByteArrayTag, IntArrayTag, LongArrayTag),
        )

    def _delete_item(self, item: NBTTreeWidgetItem) -> None:
        parent_item = item.parent()
        if not isinstance(parent_item, NBTTreeWidgetItem):
            return
        parent_tag = parent_item.get_tag()

        def update_grandparent() -> None:
            grandparent_item = parent_item.parent()
            if isinstance(grandparent_item, NBTTreeWidgetItem):
                grandparent_tag = grandparent_item.get_tag()
                if isinstance(grandparent_tag, NamedTag):
                    grandparent_item.update_text()

        if isinstance(parent_tag, CompoundTag):
            key = item.get_key()
            if key is None:
                raise RuntimeError("Item with CompoundTag parent has no key")
            parent_tag.pop(key, None)
            parent_item.removeChild(item)
            parent_item.update_text()
            if not parent_tag:
                parent_item.setExpanded(False)
            update_grandparent()
        else:
            i = parent_item.indexOfChild(item)
            if isinstance(parent_tag, ListTag):
                parent_tag.pop(i)
                parent_item.removeChild(item)
                parent_item.update_text()
            elif isinstance(parent_tag, (ByteArrayTag, IntArrayTag, LongArrayTag)):
                l: list[SupportsInt] = list(parent_tag)
                l.pop(i)
                if isinstance(parent_tag, ByteArrayTag):
                    parent_tag = ByteArrayTag(l)
                elif isinstance(parent_tag, IntArrayTag):
                    parent_tag = IntArrayTag(l)
                else:
                    parent_tag = LongArrayTag(l)
                parent_item.set_tag(parent_tag, True)
                parent_item.removeChild(item)
                parent_item.update_text()
            else:
                return
            update_grandparent()
            for i2 in range(i, parent_item.childCount()):
                child = parent_item.child(i2)
                if isinstance(child, NBTTreeWidgetItem):
                    child.update_text()
            if not parent_tag:
                parent_item.setExpanded(False)
        self._update_buttons()

    def _delete_current_item(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._delete_item(item)

    @staticmethod
    def _supports_move_up(item: NBTTreeWidgetItem) -> bool:
        parent_item = item.parent()
        return (
            isinstance(parent_item, NBTTreeWidgetItem)
            and isinstance(
                parent_item.get_tag(),
                (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag),
            )
            and 0 < parent_item.indexOfChild(item)
        )

    def _move_item_up(self, item: NBTTreeWidgetItem) -> None:
        parent_item = item.parent()
        if not isinstance(parent_item, NBTTreeWidgetItem):
            return
        i = parent_item.indexOfChild(item)
        parent_tag = parent_item.get_tag()
        if (
            isinstance(parent_tag, (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag))
            and 0 < i
        ):
            parent_tag[i - 1], parent_tag[i] = parent_tag[i], parent_tag[i - 1]
            child = parent_item.takeChild(i - 1)
            if child is not None:
                parent_item.insertChild(i, child)
                if isinstance(child, NBTTreeWidgetItem):
                    child.update_text()
            item.update_text()
            self._update_buttons()

    def _move_current_item_up(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._move_item_up(item)

    @staticmethod
    def _supports_move_down(item: NBTTreeWidgetItem) -> bool:
        parent_item = item.parent()
        return (
            isinstance(parent_item, NBTTreeWidgetItem)
            and isinstance(
                parent_item.get_tag(),
                (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag),
            )
            and parent_item.indexOfChild(item) < parent_item.childCount() - 1
        )

    def _move_item_down(self, item: NBTTreeWidgetItem) -> None:
        parent_item = item.parent()
        if not isinstance(parent_item, NBTTreeWidgetItem):
            return
        i = parent_item.indexOfChild(item)
        parent_tag = parent_item.get_tag()
        if (
            isinstance(parent_tag, (ListTag, ByteArrayTag, IntArrayTag, LongArrayTag))
            and i < parent_item.childCount() - 1
        ):
            parent_tag[i + 1], parent_tag[i] = parent_tag[i], parent_tag[i + 1]
            item_2 = parent_item.takeChild(i + 1)
            if item_2 is not None:
                parent_item.insertChild(i, item_2)
                if isinstance(item_2, NBTTreeWidgetItem):
                    item_2.update_text()
            item.update_text()
            self._update_buttons()

    def _move_current_item_down(self) -> None:
        item = self._tree.currentItem()
        if isinstance(item, NBTTreeWidgetItem):
            self._move_item_down(item)


class NBTWidget(QWidget):
    def __init__(self, tag: TagType | None = None) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._tree_widget = NBTWidgetP(NamedTag() if tag is None else tag)
        self._layout.addWidget(self._tree_widget)

    def get_tag(self) -> TagType:
        return deepcopy(self._tree_widget.get_tag())

    def set_tag(self, tag: TagType) -> None:
        self._tree_widget.set_tag(deepcopy(tag))
