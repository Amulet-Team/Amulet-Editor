from amulet_editor.models.generic._singleton_signal import SingletonSignal

_init_obj, init_editor = SingletonSignal()
_del_obj, destroy_editor = SingletonSignal()
