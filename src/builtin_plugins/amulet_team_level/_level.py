from enum import Enum
from threading import Lock

from amulet.level.abc import Level

class UnsetType(Enum):
    Unset = 0


Unset = UnsetType.Unset

_lock = Lock()
_level: UnsetType | Level | None = Unset


def get_level() -> Level | None:
    """Get the active level."""
    with _lock:
        if _level is Unset:
            raise RuntimeError("Level has not been set yet.")
        return _level


def set_level(level: Level | None) -> None:
    """
    Set the active level.
    Only the entry command can call this function.
    """
    global _level
    with _lock:
        if _level is not Unset:
            raise RuntimeError("The level has already been set.")
        _level = level
