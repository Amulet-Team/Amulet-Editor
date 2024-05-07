from __future__ import annotations

from typing import Type, Union, NamedTuple

from PySide6.QtCore import Qt

from amulet_team_main_window2._application.widget import Widget


class Layout(NamedTuple):
    first: Union[Layout, Type[Widget]]
    second: Union[Layout, Type[Widget]]
    orientation: Qt.Orientation
