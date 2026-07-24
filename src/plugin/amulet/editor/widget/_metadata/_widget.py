from __future__ import annotations

import os
import sys
import subprocess
from threading import Lock

from PySide6.QtCore import Qt, QSize, QCoreApplication, QThread, QObject, Signal
from PySide6.QtGui import QShowEvent, QHideEvent, QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)

from PIL.ImageQt import ImageQt

from amulet.utils.event import EventToken
from amulet.utils.lock import ThreadAccessMode, ThreadShareMode, LockNotAcquired
from amulet.utils.task_manager import CancelManager

from amulet.level.abc import Level, DiskLevel, ReloadableLevel
from amulet.level.java import JavaLevel
from amulet.level.bedrock import BedrockLevel

from amulet.app.invoke import invoke, enqueue

from plugin.tablericons import tablericons
from plugin.amulet.nbt.widget._widget import SVGButton

from .explorer.java import JavaLevelExplorer
from .explorer.bedrock import BedrockLevelExplorer


class LevelLocker(QObject):
    def __init__(self, level: Level):
        super().__init__()
        self._level = level
        self._level_lock_held = False
        self._lock = Lock()
        self._cancel_manager: CancelManager | None = None

    locked = Signal()

    def is_locked(self) -> bool:
        with self._lock:
            return self._level_lock_held

    def _try_lock(self, timeout: float) -> None:
        assert self._cancel_manager is not None
        locked = self._level.lock.acquire(
            timeout=timeout, cancel_manager=self._cancel_manager
        )
        with self._lock:
            self._cancel_manager = None
            self._level_lock_held = locked
        if locked:
            self.locked.emit()

    def try_lock(self, timeout: float) -> None:
        """
        Try acquiring the level lock.
        Executes asynchronously.
        locked is emitted on success.
        """
        with self._lock:
            if self._cancel_manager is not None:
                raise RuntimeError("The level is already being locked")
            self._cancel_manager = CancelManager()
        enqueue(lambda: self._try_lock(timeout), self)

    def _unlock(self) -> None:
        with self._lock:
            if not self._level_lock_held:
                return
        self._level.lock.release()
        self._level_lock_held = False

    def unlock(self) -> None:
        """Release the level lock."""
        with self._lock:
            if self._cancel_manager is not None:
                self._cancel_manager.cancel()
        invoke(self._unlock, self)


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

        self._thumbnail = QLabel()
        self._header_layout.addWidget(
            self._thumbnail, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._header_text_layout = QVBoxLayout()
        self._header_text_layout.setContentsMargins(5, 5, 5, 5)
        self._header_text_layout.setSpacing(5)
        self._header_layout.addLayout(self._header_text_layout, 1)

        self._title_label = QLabel()
        title_font = self._title_label.font()
        title_font.setPointSize(30)
        self._title_label.setFont(title_font)
        self._header_text_layout.addWidget(
            self._title_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self._version_label = QLabel()
        subtitle_font = self._version_label.font()
        subtitle_font.setPointSize(16)
        self._version_label.setFont(subtitle_font)
        self._header_text_layout.addWidget(
            self._version_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        if isinstance(self._level, DiskLevel):
            path_button = SVGButton(
                tablericons.outline.file
                if os.path.isfile(self._level.path)
                else tablericons.outline.folder
            )
            path_button.clicked.connect(self._open_level_folder)
            path_button.setFixedSize(QSize(35, 35))
            path_label = QLabel(self._level.path)
            path_label.setMinimumWidth(0)
            path_label.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            path_label.setFont(subtitle_font)

            path_layout = QHBoxLayout()
            self._header_text_layout.addLayout(path_layout)
            path_layout.addWidget(path_button)
            path_layout.addSpacing(5)
            path_layout.addWidget(path_label, 1)

        self._header_text_layout.addStretch(1)

        self._explorer: BedrockLevelExplorer | JavaLevelExplorer | None = None
        if isinstance(self._level, JavaLevel):
            self._explorer = java_level_explorer = JavaLevelExplorer(self._level)
            self._layout.addWidget(java_level_explorer, 1)
        elif isinstance(self._level, BedrockLevel):
            self._explorer = bedrock_level_explorer = BedrockLevelExplorer()
            self._layout.addWidget(bedrock_level_explorer, 1)
        else:
            self._layout.addStretch(1)

        self._level_reload_token: EventToken[()] | None = None
        self._level_name_changed_token: EventToken[str] | None = None

        self._lock_thread = QThread()
        self._level_locker = LevelLocker(level)
        self._level_locker.moveToThread(self._lock_thread)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._try_update_display()
        if self._explorer is not None:
            self._explorer.setEnabled(False)
        # The level events may be called by any thread with the level lock held.
        self._level_name_changed_token = self._level.level_name_changed.connect(
            self._set_title
        )
        if isinstance(self._level, ReloadableLevel):
            # reloaded events are called with the lock so we don't need to acquire it
            self._level_reload_token = self._level.reloaded.connect(
                self._try_update_display_threadsafe
            )
        self._lock_thread.start()
        self._level_locker.locked.connect(self._on_locked)
        self._level_locker.try_lock(1.0)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self._level.level_name_changed.disconnect(self._level_name_changed_token)
        if self._level_reload_token is not None and isinstance(
            self._level, ReloadableLevel
        ):
            self._level.reloaded.disconnect(self._level_reload_token)
            self._level_reload_token = None
        self._level_locker.locked.disconnect(self._on_locked)
        self._level_locker.unlock()
        self._lock_thread.quit()
        self._lock_thread.wait()

    def _on_locked(self) -> None:
        if self._explorer is not None:
            self._explorer.setEnabled(True)
            self._explorer.reload()

    def _try_update_display_threadsafe(self) -> None:
        enqueue(self._try_update_display, self)

    def _try_update_display(self) -> None:
        """Try and acquire the level lock and update the display."""
        if self._level_locker.is_locked():
            self._update_display()
        else:
            try:
                with self._level.lock(
                    timeout=0.2,
                    thread_mode=(
                        ThreadAccessMode.Read,
                        ThreadShareMode.SharedReadWrite,
                    ),
                ):
                    self._update_display()
            except LockNotAcquired:
                pass

    def _update_display(self) -> None:
        """
        Update the display.
        Must be called with the level lock in ReadWrite mode.
        """
        thumbnail = self._level.thumbnail
        self._thumbnail.setPixmap(
            QPixmap.fromImage(ImageQt(thumbnail)).scaled(
                int(200 * thumbnail.width / thumbnail.height),
                200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )
        self._title_label.setText(self._level.level_name)
        self._version_label.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.MetadataTool", "version", None
            ).format(self._level.max_game_version)
        )

    def _set_title(self, title: str) -> None:
        enqueue(lambda: self._title_label.setText(title), self._title_label)

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


class MetadataTool(QWidget):
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
