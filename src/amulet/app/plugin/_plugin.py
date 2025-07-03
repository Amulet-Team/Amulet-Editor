from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class PluginV1:
    load: Callable[[], None] = lambda: None
    unload: Callable[[], None] = lambda: None
