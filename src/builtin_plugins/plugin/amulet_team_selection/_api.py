from amulet.core.selection import SelectionGroup
from amulet.app._signal import create_signal


_selection: SelectionGroup = SelectionGroup()

_selection_changed_obj, selection_changed = create_signal(SelectionGroup)


def get_selection() -> SelectionGroup:
    return _selection


def set_selection(selection: SelectionGroup) -> None:
    global _selection
    _selection = selection
    selection_changed.emit(selection)
