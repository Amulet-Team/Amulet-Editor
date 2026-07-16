from __future__ import annotations

import os
import sys
import subprocess
import weakref
from threading import Condition
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    Qt,
    QEvent,
    QThreadPool,
    QThread,
    QCoreApplication,
    QSize,
    Signal,
)
from PySide6.QtGui import QShowEvent, QHideEvent, QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QSpinBox,
    QSizePolicy,
    QMessageBox,
)

from PIL.ImageQt import ImageQt

from amulet.utils.task_manager import CancelManager
from amulet.utils.lock import ThreadAccessMode, ThreadShareMode, LockNotAcquired

from amulet.nbt import NamedTag

from amulet.level.abc import Level, DiskLevel
from amulet.level.java import JavaLevel
from amulet.level.bedrock import BedrockLevel, BedrockLevelDat

from amulet.app.exception import CatchExceptionDialog
from amulet.app.qt.signal import TypeFormSignal

from plugin.tablericons import tablericons
from plugin.amulet.nbt.widget import NBTWidget
from plugin.amulet.nbt.widget._widget import SVGButton

from plugin.amulet.editor._tab import ToolAboutToHide


class Thread(QThread):
    _run = TypeFormSignal(Callable[[], Any])

    def __init__(self) -> None:
        super().__init__()
        self._run.connect(self._on_run, type=Qt.ConnectionType.BlockingQueuedConnection)
        self.moveToThread(self)
        self.start()

    @staticmethod
    def _on_run(func: Callable[[], Any]) -> None:
        with CatchExceptionDialog("Error running function in thread."):
            func()

    def submit(self, func: Callable[[], Any]) -> None:
        self._run.emit(func)


class LevelDatEditor(QWidget):
    saved = Signal()

    def __init__(self, level: JavaLevel | BedrockLevel):
        super().__init__()
        self._level = level
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._nbt_widget = NBTWidget()
        self._layout.addWidget(self._nbt_widget)

        self._reload_button = SVGButton(tablericons.outline.reload)
        self._reload_button.setFixedSize(QSize(30, 30))
        self._reload_button.clicked.connect(self._reload)
        self._nbt_widget.add_menu_widget(self._reload_button)

        self._save_button = SVGButton(tablericons.outline.device_floppy)
        self._save_button.setFixedSize(QSize(30, 30))
        self._save_button.clicked.connect(self.save)
        self._save_button.clicked.connect(self.saved)
        self._nbt_widget.add_menu_widget(self._save_button)

        self._dat_version_meta_widget = QWidget()
        self._dat_version_meta_widget.setVisible(isinstance(level, BedrockLevel))
        self._nbt_widget.add_menu_widget(self._dat_version_meta_widget)

        self._dat_version_meta_layout = QHBoxLayout(self._dat_version_meta_widget)
        self._dat_version_meta_layout.setContentsMargins(0, 0, 0, 0)
        self._dat_version_meta_layout.addSpacing(10)

        self._dat_version_label = QLabel()
        font = self._dat_version_label.font()
        font.setPointSize(12)
        self._dat_version_label.setFont(font)
        self._dat_version_meta_layout.addWidget(
            self._dat_version_label, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self._dat_version_spin = QSpinBox(minimum=-(2**31), maximum=2**31 - 1)
        self._dat_version_spin.setFixedHeight(30)
        self._dat_version_meta_layout.addWidget(self._dat_version_spin)

        self._lock_acquired.connect(self._set_level_dat)

        self._lock_condition = Condition()
        self._level_locked = False
        self._level_lock_cancel_manager: CancelManager | None = None

        # The level must be locked and unlocked in this thread
        self._lock_thread = lock_thread = Thread()
        weak_self = weakref.ref(self)

        def on_destroyed() -> None:
            self_ = weak_self()
            if self_ is not None:
                self_._release_level_lock()
            lock_thread.quit()

        self.destroyed.connect(on_destroyed)

        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self._dat_version_label.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.LevelDatEditor", "level_dat_version", None
            )
        )

    def save(self) -> None:
        tag = self._nbt_widget.get_tag()
        if not isinstance(tag, NamedTag):
            tag = NamedTag(tag, "")
        if isinstance(self._level, BedrockLevel):
            version = self._dat_version_spin.value()
            self._level.raw_level.level_dat = BedrockLevelDat(version, tag)
        else:
            self._level.raw_level.level_dat = tag

    def _reload(self) -> None:
        level_dat = self._level.raw_level.level_dat
        self._set_level_dat(level_dat)

    _lock_acquired = TypeFormSignal(NamedTag | BedrockLevelDat)

    def _set_level_dat(self, level_dat: NamedTag | BedrockLevelDat) -> None:
        """
        Populate the GUI with the level.dat.
        The level lock must be held when this is called.
        """
        if isinstance(level_dat, BedrockLevelDat):
            self._dat_version_spin.setValue(level_dat.version)
            level_dat = level_dat.named_tag
            self._dat_version_meta_widget.show()
        else:
            self._dat_version_meta_widget.hide()
        self._nbt_widget.set_tag(level_dat)
        self._nbt_widget.setEnabled(True)

    def _try_acquire_level_lock(self) -> None:
        """
        Try and acquire the level lock (waiting for up to 1 second).
        If the lock is acquired, _lock_acquired is emitted.
        This is thread safe.
        """
        with self._lock_condition:
            while self._level_lock_cancel_manager is not None:
                # Level is being locked.
                self._lock_condition.wait()
            if self._level_locked:
                return
            self._level_lock_cancel_manager = cancel_manager = CancelManager()

        # OrderedMutex must be locked and unlocked from the same thread.
        locked: bool | None = None

        def acquire() -> None:
            nonlocal locked
            locked = self._level.lock.acquire(
                timeout=1.0, cancel_manager=cancel_manager
            )

        self._lock_thread.submit(acquire)

        if locked:
            level_dat = self._level.raw_level.level_dat
            self._lock_acquired.emit(level_dat)

        with self._lock_condition:
            self._level_lock_cancel_manager = None
            self._level_locked = locked or False
            self._lock_condition.notify_all()

    def _release_level_lock(self) -> None:
        """Cancels pending acquires and releases the level lock."""
        with self._lock_condition:
            if self._level_lock_cancel_manager is not None:
                self._level_lock_cancel_manager.cancel()
                while self._level_lock_cancel_manager is not None:
                    # Level is being locked.
                    self._lock_condition.wait()
            if self._level_locked:
                self._lock_thread.submit(self._level.lock.release)
                self._level_locked = False

    def showEvent(self, event: QShowEvent) -> None:
        self._nbt_widget.setEnabled(False)
        super().showEvent(event)
        QThreadPool.globalInstance().start(self._try_acquire_level_lock)

    def hideEvent(self, event: QHideEvent) -> None:
        self._release_level_lock()
        super().hideEvent(event)

    def has_unsaved_changes(self) -> bool:
        return self._save_button.isEnabled()

    def ask_save(self) -> int:
        """
        If there are unsaved changes, ask the user if they want to save them.
        If the user chooses to save, the changes are written to the level.

        :return: QMessageBox.StandardButton.Save|Discard|Cancel depending on the user's choice.
        """
        if self.has_unsaved_changes():
            message_box = QMessageBox(
                text=QCoreApplication.translate(
                    "plugin.amulet.editor.LevelDatEditor", "ask_save", None
                ),
                standardButtons=QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            code = message_box.exec()
            if code == QMessageBox.StandardButton.Save:
                self.save()
            return code
        return QMessageBox.StandardButton.Discard


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
