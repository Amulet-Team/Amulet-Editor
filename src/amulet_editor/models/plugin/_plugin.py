from typing import Callable, NamedTuple


class PluginV1(NamedTuple):
    load: Callable[[], None] = lambda: None
    unload: Callable[[], None] = lambda: None
