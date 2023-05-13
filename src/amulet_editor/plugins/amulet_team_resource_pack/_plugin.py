from typing import Optional
from minecraft_model_reader import BaseResourcePackManager
from PySide6.QtCore import QObject, Signal


class RPObj(QObject):
    resource_pack_changed = Signal()


_rpobj = RPObj()

resource_pack_changed = _rpobj.resource_pack_changed


_rp: Optional[BaseResourcePackManager] = None


def get_resource_pack() -> BaseResourcePackManager:
    """
    Get the active resource pack.
    This will raise a runtime error until the resource pack is first set.
    """
    if _rp is None:
        raise RuntimeError("Resource pack has not been set yet.")
    return _rp


def set_resource_pack(resource_pack: BaseResourcePackManager):
    """
    Set the resource pack.
    Will emit a signal from resource_pack_changed

    :param resource_pack: The resource pack to set.
    """
    global _rp
    if not isinstance(resource_pack, BaseResourcePackManager):
        raise TypeError("resource_pack must be an instance of BaseResourcePackManager")
    _rp = resource_pack
    resource_pack_changed.emit()
