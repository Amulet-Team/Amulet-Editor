"""
This module manages resource pack objects for each level
"""

from weakref import WeakKeyDictionary
from threading import Lock, RLock
from typing import Optional
import logging

from PySide6.QtCore import QObject, QCoreApplication, Signal

from amulet.api.level import BaseLevel
from amulet_editor.models.generic._promise import Promise
from amulet_editor.models.widgets.traceback_dialog import DisplayException

from minecraft_model_reader import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack import (
    load_resource_pack_manager,
)
from minecraft_model_reader.api.resource_pack.java.download_resources import (
    get_java_vanilla_latest_iter,
    get_java_vanilla_fix,
)

log = logging.getLogger(__name__)


class ResourcePackContainer(QObject):
    # Emitted with a promise object when a resource pack change is started.
    changing = Signal(object)  # Promise[None]
    # Emitted when the resource pack has changed.
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._lock = RLock()
        self._resource_pack: Optional[BaseResourcePackManager] = None
        self._loader: Optional[Promise[None]] = None

    @property
    def loader(self) -> Optional[Promise[None]]:
        """
        If the resource pack is being loaded this will be a promise.
        This can be used to update a GUI to show the progress.
        :return: A Promise instance if a resource pack is being loaded otherwise None.
        """
        return self._loader

    @property
    def loaded(self) -> bool:
        """
        Is there a valid resource pack.
        :return: True if loaded otherwise False.
        """
        return self._resource_pack is not None

    @property
    def resource_pack(self) -> BaseResourcePackManager:
        """
        :return: The active resource pack for this level.
        :raises RuntimeError: If the resource pack has not been initialised yet.
        """
        rp = self._resource_pack
        if rp is None:
            raise RuntimeError(
                "The ResourcePackManager for this level has not been loaded yet."
            )
        return rp

    def init(self):
        """
        Initialise the default resource pack for this level if one does not already exist.
        This is completed asynchronously. A promise is emitted from changing.

        >>> def load(level: BaseLevel):
        >>>     container = get_resource_pack_container(level)
        >>>     promise = container.init(level)
        >>>     def on_ready():
        >>>         print("finished")
        >>>         if promise.get_return():
        >>>             print("resource pack was already loaded")
        >>>         else:
        >>>             print("resource pack has been loaded.")
        >>>     promise.ready.connect(on_ready)
        >>>     promise.progress_change.connect(lambda progress: print(progress))
        >>>     promise.start()
        """

        def init(promise_data: Promise.Data) -> bool:
            with self._lock, DisplayException("Error initialising the resource pack."):
                if self._resource_pack is None:
                    # TODO: support other resource pack formats
                    promise_data.progress_text_change.emit(
                        QCoreApplication.translate(
                            "ResourcePack", "downloading_resource_pack", None
                        )
                    )
                    try:
                        it = get_java_vanilla_latest_iter()
                        while True:
                            progress = next(it)
                            promise_data.progress_change.emit(progress * 0.5)
                            if promise_data.is_cancel_requested():
                                raise Promise.OperationCanceled()
                    except StopIteration as e:
                        vanilla = e.value

                    self._resource_pack = load_resource_pack_manager(
                        [vanilla, get_java_vanilla_fix()], load=False
                    )
                    promise_data.progress_text_change.emit(
                        QCoreApplication.translate(
                            "ResourcePack", "loading_resource_pack", None
                        )
                    )
                    for progress in self._resource_pack.reload():
                        promise_data.progress_change.emit(0.5 + progress * 0.5)
                    self.changed.emit()
                    log.debug("Loaded resource pack.")
                    return False
                return True

        promise_ = Promise[bool](init)
        old_loader = self._loader
        if old_loader is not None:
            old_loader.cancel()
        self._loader = promise_
        self.changing.emit(promise_)
        promise_.start()

    # def set_resource_pack(self, resource_pack: BaseResourcePackManager):
    #     """
    #     Set the resource pack.
    #     Will emit a signal from changed after setting
    #
    #     :param resource_pack: The resource pack to set.
    #     """
    #     if not isinstance(resource_pack, BaseResourcePackManager):
    #         raise TypeError("resource_pack must be an instance of BaseResourcePackManager")
    #     with self._lock:
    #         self._resource_pack = resource_pack
    #         self.changed.emit()


_lock = Lock()
_level_data: WeakKeyDictionary[BaseLevel, ResourcePackContainer] = WeakKeyDictionary()


def get_resource_pack_container(level: BaseLevel) -> ResourcePackContainer:
    with _lock:
        if level not in _level_data:
            _level_data[level] = ResourcePackContainer()
        return _level_data[level]
