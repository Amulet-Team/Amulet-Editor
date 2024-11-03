from amulet.selection import SelectionGroup
from amulet_editor.models.generic._singleton_signal import SingletonSignal


_selection: SelectionGroup = SelectionGroup()

_selection_changed_obj, selection_changed = SingletonSignal(SelectionGroup)


def get_selection() -> SelectionGroup:
    return _selection


def set_selection(selection: SelectionGroup) -> None:
    global _selection
    _selection = selection
    selection_changed.emit(selection)
