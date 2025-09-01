from threading import Lock

from amulet.core.selection import SelectionBoxGroup, SelectionShapeGroup
from amulet.app._signal import create_signal

_lock = Lock()

_selection: SelectionBoxGroup | SelectionShapeGroup = SelectionBoxGroup()

_selection_changed_obj, selection_changed = create_signal(SelectionBoxGroup | SelectionShapeGroup)


def get_selection() -> SelectionBoxGroup | SelectionShapeGroup:
    with _lock:
        return _selection


def set_selection(selection: SelectionBoxGroup | SelectionShapeGroup) -> None:
    global _selection
    with _lock:
        _selection = selection
    selection_changed.emit(selection)
