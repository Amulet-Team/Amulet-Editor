import os

from PySide6.QtGui import QPixmap, QIcon

from amulet.nbt import (
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
)

type TagType = NamedTag | AnyNBT

_icons: dict[type[TagType], tuple[QPixmap, QIcon]] = {}


def _load_icons() -> None:
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
            pixmap = icon_sheet.copy(32 * x, 32 * y, 32, 32)
            _icons[cls] = pixmap, QIcon(pixmap)


def get_pixmap(tag_cls: type[TagType]) -> QPixmap | None:
    _load_icons()
    return _icons.get(tag_cls, (None, None))[0]


def get_icon(tag_cls: type[TagType]) -> QIcon | None:
    _load_icons()
    return _icons.get(tag_cls, (None, None))[1]
