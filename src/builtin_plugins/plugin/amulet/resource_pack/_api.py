"""
This module manages resource pack objects for each level
"""

from weakref import WeakKeyDictionary
from threading import Lock, Condition
import logging
import traceback

from PySide6.QtCore import QObject, QCoreApplication, Signal

from amulet.level.abc import Level
from amulet.app.exception import display_exception

from amulet.utils.task_manager import AbstractProgressManager, VoidProgressManager
from amulet.resource_pack.abc import BaseResourcePackManager
from amulet.resource_pack import load_resource_pack_manager
from amulet.resource_pack.java.download_resources import (
    get_java_vanilla_latest,
    get_java_vanilla_fix,
)

log = logging.getLogger(__name__)


class ResourcePackHandle(QObject):
    # Emitted when the resource pack has changed.
    changed = Signal(BaseResourcePackManager)

    def __init__(self) -> None:
        super().__init__()
        self._condition = Condition(Lock())
        self._resource_pack: BaseResourcePackManager | None = None
        self._load_progress_manager: AbstractProgressManager | None = None

    def __del__(self) -> None:
        log.debug("ResourcePackHandle.__del__")

    def get_resource_pack(
        self,
        progress_manager: AbstractProgressManager = VoidProgressManager(),
    ) -> BaseResourcePackManager:
        """
        The active resource pack for this level.
        If the resource pack has not been loaded/set, this will block until it is loaded.
        If it is called again before the first call is finished it will block until the first call is finished.
        """
        with self._condition:
            if self._load_progress_manager is not None:
                # The resource pack is being loaded by another call.
                # Connect the progress managers
                progress_token = self._load_progress_manager.register_progress_callback(
                    progress_manager.update_progress
                )
                progress_text_token = (
                    self._load_progress_manager.register_progress_text_callback(
                        progress_manager.update_progress_text
                    )
                )

                # Wait until the first call completes. Note that it may fail.
                while self._load_progress_manager is not None:
                    self._condition.wait()

                self._load_progress_manager.unregister_progress_callback(progress_token)
                self._load_progress_manager.unregister_progress_text_callback(
                    progress_text_token
                )

            if self._resource_pack is None:
                # The resource pack has not been loaded
                self._load_progress_manager = progress_manager
            else:
                # The resource pack has already been set/loaded
                return self._resource_pack

        try:
            # TODO: support other resource pack formats
            progress_manager.update_progress_text(
                QCoreApplication.translate(
                    "ResourcePack", "downloading_resource_pack", None
                )
            )

            download_progress_manager = progress_manager.get_child(0.0, 0.5)
            vanilla = get_java_vanilla_latest(download_progress_manager)

            resource_pack = load_resource_pack_manager(
                [vanilla, get_java_vanilla_fix()], load=False
            )
            progress_manager.update_progress_text(
                QCoreApplication.translate(
                    "ResourcePack", "loading_resource_pack", None
                )
            )
            reload_progress_manager = progress_manager.get_child(0.5, 1.0)
            resource_pack.reload(reload_progress_manager)
        except Exception as e:
            # Loading failed
            display_exception(
                title="Error initialising the resource pack.",
                error=str(e),
                traceback=traceback.format_exc(),
            )
            with self._condition:
                self._load_progress_manager = None
                self._condition.notify_all()
            # re-raise the exception
            raise
        else:
            # Loading succeeded
            with self._condition:
                self._load_progress_manager = None
                self._resource_pack = resource_pack
                self._condition.notify_all()
            log.debug("Loaded resource pack.")
            return resource_pack

    def set_resource_pack(self, resource_pack: BaseResourcePackManager) -> None:
        """
        Set the resource pack.
        Will emit a signal from changed after setting

        :param resource_pack: The resource pack to set.
        """
        if not isinstance(resource_pack, BaseResourcePackManager):
            raise TypeError(
                "resource_pack must be an instance of BaseResourcePackManager"
            )
        with self._condition:
            # Wait for loading operations to finish.
            # TODO: add the ability to cancel the loading operation so we don't need to wait for it to finish.
            while self._load_progress_manager is not None:
                self._condition.wait()
            if resource_pack is self._resource_pack:
                return
            self._resource_pack = resource_pack
        self.changed.emit(self._resource_pack)


_lock = Lock()
_level_data: WeakKeyDictionary[Level, ResourcePackHandle] = WeakKeyDictionary()


def get_resource_pack_handle(level: Level) -> ResourcePackHandle:
    with _lock:
        if level not in _level_data:
            _level_data[level] = ResourcePackHandle()
        return _level_data[level]
