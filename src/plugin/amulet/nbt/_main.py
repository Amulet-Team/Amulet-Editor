from __future__ import annotations

from typing import NoReturn, cast
from argparse import Namespace
import logging
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from amulet.nbt import (
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
    AnyNBT,
)

from amulet.app import __version__
from amulet.app.resource import get_resource_path

from amulet.app.app import app_created
from amulet.app.style import set_style

from ._locale import load_translations
from .widget import NBTWidget

log = logging.getLogger(__name__)


class EditorNamespace(Namespace):
    level_paths: list[str]


def main(argv: list[str]) -> NoReturn:
    # Check an app has not already been created
    if QApplication.instance() is not None:
        raise RuntimeError("QApplication has already been initialized")

    # Initialise the application
    app = QApplication()
    app_created.emit()
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(get_resource_path("icons/amulet/Icon.ico")))

    set_style("amulet")

    load_translations()

    app.setApplicationName(QApplication.translate("plugin.amulet.nbt", "app_name"))

    tags = [
        # ByteTag(1),
        # ShortTag(2),
        # IntTag(3),
        # LongTag(4),
        # FloatTag(5.0),
        # DoubleTag(6.0),
        # ByteArrayTag([1, 2, 3]),
        # StringTag("Hello, world!"),
        # ListTag([IntTag(1), IntTag(2), IntTag(3)]),
        # CompoundTag(),
        # IntArrayTag([1, 2, 3]),
        # LongArrayTag([1, 2, 3]),
        NamedTag(
            CompoundTag(
                cast(
                    dict[str | bytes, AnyNBT],
                    {
                        "ByteTag": ByteTag(1),
                        "ShortTag": ShortTag(2),
                        "IntTag": IntTag(3),
                        "LongTag": LongTag(4),
                        "FloatTag": FloatTag(5.0),
                        "DoubleTag": DoubleTag(6.0),
                        "ByteArrayTag": ByteArrayTag([1, 2, 3]),
                        "StringTag": StringTag("Hello, world!"),
                        "ListTag": ListTag([IntTag(1), IntTag(2), IntTag(3)]),
                        "CompoundTag": CompoundTag(),
                        "IntArrayTag": IntArrayTag([1, 2, 3]),
                        "LongArrayTag": LongArrayTag([1, 2, 3]),
                        b"\xff": StringTag(b"\xff"),
                    },
                )
            ),
            "test",
        ),
    ]

    widgets = []
    for tag in tags:
        widget = NBTWidget(tag)
        widgets.append(widget)
        widget.show()

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
