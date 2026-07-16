from __future__ import annotations

import os
import sys
import subprocess

from PySide6.QtCore import (
    Qt,
    QSize,
)
from PySide6.QtGui import QShowEvent, QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QMessageBox,
)

from PIL.ImageQt import ImageQt

from amulet.utils.lock import ThreadAccessMode, ThreadShareMode, LockNotAcquired

from amulet.level.abc import Level, DiskLevel
from amulet.level.java import JavaLevel
from amulet.level.bedrock import BedrockLevel

from plugin.tablericons import tablericons
from plugin.amulet.nbt.widget._widget import SVGButton

from plugin.amulet.editor._tab import ToolAboutToHide

from .dat_editor import LevelDatEditor


class MetadataWidgetP(QWidget):
    def __init__(self, level: Level):
        super().__init__()
        self._level = level

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._header_layout)

        thumbnail = level.thumbnail
        self._thumbnail = QLabel(pixmap=QPixmap.fromImage(ImageQt(thumbnail)))
        self._thumbnail.setScaledContents(True)
        self._thumbnail.setFixedSize(int(200 * thumbnail.width / thumbnail.height), 200)
        self._header_layout.addWidget(
            self._thumbnail, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._header_text_layout = QVBoxLayout()
        self._header_text_layout.setContentsMargins(5, 5, 5, 5)
        self._header_text_layout.setSpacing(5)
        self._header_layout.addLayout(self._header_text_layout, 1)

        self._title_label = QLabel()
        font = self._title_label.font()
        font.setPointSize(30)
        self._title_label.setFont(font)
        self._header_text_layout.addWidget(
            self._title_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        try:
            with self._level.lock(
                timeout=0.2,
                thread_mode=(ThreadAccessMode.Read, ThreadShareMode.SharedReadWrite),
            ):
                self._update_display()
        except LockNotAcquired:
            pass

        if isinstance(level, DiskLevel):
            path_button = SVGButton(
                tablericons.outline.file
                if os.path.isfile(level.path)
                else tablericons.outline.folder
            )
            path_button.clicked.connect(self._open_level_folder)
            path_button.setFixedSize(QSize(35, 35))
            path_label = QLabel(level.path)
            path_label.setMinimumWidth(0)
            path_label.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            font = path_label.font()
            font.setPointSize(16)
            path_label.setFont(font)

            path_layout = QHBoxLayout()
            self._header_text_layout.addLayout(path_layout)
            path_layout.addWidget(path_button)
            path_layout.addSpacing(5)
            path_layout.addWidget(path_label, 1)

        self._header_text_layout.addStretch(1)

        if isinstance(self._level, (JavaLevel, BedrockLevel)):
            self._level_dat_editor: LevelDatEditor | None = LevelDatEditor(self._level)
            self._level_dat_editor.saved.connect(self._update_display)
            self._layout.addWidget(self._level_dat_editor, 1)
        else:
            self._level_dat_editor = None
            self._layout.addStretch(1)

    def _update_display(self) -> None:
        """
        Update the display.
        Must be called with the level lock in ReadWrite mode.
        """
        self._title_label.setText(self._level.level_name)

    def _open_level_folder(self) -> None:
        if isinstance(self._level, DiskLevel):
            path = self._level.path
            if os.path.isfile(path):
                path = os.path.dirname(path)
            if os.path.isdir(path):
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path])
                else:
                    subprocess.run(["xdg-open", path])

    def hideable(self) -> bool:
        return (
            self._level_dat_editor is None
            or self._level_dat_editor.ask_save() != QMessageBox.StandardButton.Cancel
        )


class MetadataTool(QWidget, ToolAboutToHide):
    def __init__(self, level: Level):
        super().__init__()
        self._level = level
        self._widget: MetadataWidgetP | None = None

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._widget is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self._widget = MetadataWidgetP(self._level)
            layout.addWidget(self._widget)

    def tool_about_to_hide(self) -> bool:
        return self._widget is None or self._widget.hideable()
