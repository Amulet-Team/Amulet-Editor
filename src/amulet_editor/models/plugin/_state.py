from __future__ import annotations

from enum import IntEnum


class PluginState(IntEnum):
    Disabled = 0  # Plugin is not enabled by the user
    Inactive = (
        1  # Plugin is enabled by the user but had dependencies that are not enabled
    )
    Enabled = 2  # Plugin is fully enabled
