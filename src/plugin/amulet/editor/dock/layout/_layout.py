"""
Classes to configure the layout of the docking system.
"""

from __future__ import annotations
from dataclasses import dataclass

from PySide6.QtCore import Qt, QPoint, QSize


@dataclass(frozen=True)
class WidgetConfig:
    identifier: str


@dataclass(frozen=True)
class WidgetStackConfig:
    widgets: tuple[WidgetConfig, ...]


@dataclass(frozen=True)
class SplitterConfig:
    first: SplitterConfig | WidgetStackConfig
    second: SplitterConfig | WidgetStackConfig
    orientation: Qt.Orientation
    weight: float


@dataclass(frozen=True)
class WindowConfig:
    origin: QPoint | None
    size: QSize | None
    layout: SplitterConfig | WidgetStackConfig


@dataclass(frozen=True)
class LayoutConfig:
    main_window: WindowConfig
    sub_windows: tuple[WindowConfig, ...]
