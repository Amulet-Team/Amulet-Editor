from weakref import WeakKeyDictionary
from threading import Lock

from PySide6.QtCore import QObject, SignalInstance, QCoreApplication

from amulet.api.level import BaseLevel
from amulet_editor.models.generic._singleton_signal import SingletonSignal
from amulet_editor.models.generic._promise import Promise
from amulet_editor.models.generic._key_lock import KeyLock

from minecraft_model_reader import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack import (
    load_resource_pack_manager,
)
from minecraft_model_reader.api.resource_pack.java.download_resources import (
    get_java_vanilla_latest_iter,
    get_java_vanilla_fix,
)


# Each resource pack is unique to the level
_level_locks = KeyLock()
_resource_packs: WeakKeyDictionary[BaseLevel, BaseResourcePackManager] = WeakKeyDictionary()

_signals_lock = Lock()
_signals: WeakKeyDictionary[BaseLevel, tuple[QObject, SignalInstance]] = WeakKeyDictionary()


def resource_pack_changed(level: BaseLevel) -> SignalInstance:
    """Get a Qt SignalInstance that will be emitted when the resource pack for that level changes."""
    with _signals_lock:
        if level not in _signals:
            _signals[level] = SingletonSignal()
        return _signals.get(level)[1]


def init_resource_pack(level: BaseLevel) -> Promise[None]:
    """
    An asynchronous loading function for the default resource pack.
    The resource_pack_changed for the level will be emitted when loaded.
    If the resource pack is already loaded this will do nothing.

    >>> promise = init_resource_pack(level)
    >>> promise.ready.connect(lambda: print("finished"))
    >>> promise.progress_change.connect(lambda progress: print(progress))
    >>> promise.start()
    """
    def init(promise_data: Promise.Data):
        with _level_locks.get(level):
            if _resource_packs.get(level) is None:
                # TODO: support other resource pack formats
                promise_data.progress_text_change.emit(QCoreApplication.translate("ResourcePack", "downloading_resource_pack", None))
                try:
                    it = get_java_vanilla_latest_iter()
                    while True:
                        progress = next(it)
                        promise_data.progress_change.emit(progress)
                        if promise_data.is_cancel_requested():
                            raise Promise.OperationCanceled()
                except StopIteration as e:
                    vanilla = e.value

                _resource_packs[level] = load_resource_pack_manager(
                    [
                        vanilla,
                        get_java_vanilla_fix()
                    ],
                    load=False
                )
                resource_pack_changed(level).emit()

    return Promise(init)


def has_resource_pack(level: BaseLevel) -> bool:
    return _resource_packs.get(level) is not None


def get_resource_pack(level: BaseLevel) -> BaseResourcePackManager:
    """
    Get the resource pack for the level.
    Will raise RuntimeError if the resource pack for the level has not been initialised.
    You should use init_resource_pack before calling this for the first time to make sure one is initialised.
    """
    rp = _resource_packs.get(level)
    if rp is None:
        raise RuntimeError("The resource pack for this level has not been initialised yet.")
    return rp


def set_resource_pack(level: BaseLevel, resource_pack: BaseResourcePackManager):
    """
    Set the resource pack.
    Will emit a signal from resource_pack_changed after setting

    :param level: The level the resource pack is associated with.
    :param resource_pack: The resource pack to set.
    """
    if not isinstance(resource_pack, BaseResourcePackManager):
        raise TypeError("resource_pack must be an instance of BaseResourcePackManager")
    with _level_locks.get(level):
        _resource_packs[level] = resource_pack
        resource_pack_changed(level).emit()
