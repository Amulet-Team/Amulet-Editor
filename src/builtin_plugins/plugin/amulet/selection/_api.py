from threading import RLock

from PySide6.QtCore import QObject
from amulet.core.selection import SelectionShapeGroup
from amulet.app.qt.signal import Signal


class SelectionManager(QObject):
    selection_changed = Signal[SelectionShapeGroup]()
    selection_index_changed = Signal[int]()

    def __init__(self) -> None:
        super().__init__()
        self._lock = RLock()
        self._selection = SelectionShapeGroup()
        self._selection_index = -1

    def get_lock(self) -> RLock:
        return self._lock

    def get_selection(self) -> SelectionShapeGroup:
        return self._selection

    def set_selection(self, selection: SelectionShapeGroup) -> None:
        with self._lock:
            self._selection = selection
            self.selection_changed.emit(selection)
            self.set_selection_index(self._selection_index)

    def get_selection_index(self) -> int:
        return self._selection_index

    def set_selection_index(self, index: int) -> None:
        with self._lock:
            if self._selection:
                index = max(0, min(len(self._selection) - 1, index))
            else:
                index = -1
            if self._selection_index != index:
                self._selection_index = index
                self.selection_index_changed.emit(index)


_manager = SelectionManager()
get_lock = _manager.get_lock
get_selection = _manager.get_selection
set_selection = _manager.set_selection
selection_changed = _manager.selection_changed
get_selection_index = _manager.get_selection_index
set_selection_index = _manager.set_selection_index
selection_index_changed = _manager.selection_index_changed
