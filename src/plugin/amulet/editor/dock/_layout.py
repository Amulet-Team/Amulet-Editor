"""
Classes and functions to manage the docking system.
"""

from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
import re

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


# my_namespace.my_layout
# my_namespace.my_group.my_layout
LayoutIdPattern = re.compile(r"[a-z0-9_]+\.[a-z0-9_.]+")


@dataclass
class LayoutContainer:
    layout_id: str
    default_config: LayoutConfig
    layout_config: LayoutConfig


# The lock must be acquired before reading/writing the objects below.
_lock = Lock()
# The layouts that have been registered
_layouts = dict[str, LayoutContainer]()


def _get_layout_container(layout_id: str) -> LayoutContainer:
    """Get the layout container for the given layout id.

    The lock must be acquired before calling this.

    :param layout_id: The layout id to get.
    :raises ValueError: If the layout has not been registered.
    :return:
    """
    layout_container = _layouts.get(layout_id, None)
    if layout_container is None:
        raise ValueError(f"No registered layout for id {layout_id}")
    return layout_container


def register_layout(layout_id: str, default_layout: LayoutConfig) -> None:
    """Register a new layout.

    This must be called before a layout can be activated.

    :param layout_id: The unique identifier for the layout.
        The unique id must contain a namespace and layout name separated by "."
        It may contain other names separated by "."
        Names must only contain lower case a-z, 0-9 and _ characters.
        Eg "my_namespace.my_layout" or "my_namespace.my_group.my_layout"
        This is used to reference the layout.
    :param default_layout: The default layout to use.
        If the user has made changes to the layout, the changes will be displayed.
    """
    if LayoutIdPattern.fullmatch(layout_id) is None:
        raise ValueError(f"Invalid identifier {layout_id}")
    with _lock:
        if layout_id in _layouts:
            raise ValueError(f"Layout id {layout_id} has already been registered.")
        layout = read_layout_config(layout_id, default_layout)
        layout_container = LayoutContainer(layout_id, default_layout, layout)
        _layouts[layout_id] = layout_container


def get_layout(layout_id: str) -> LayoutConfig:
    """Get the layout configuration for the given layout id."""
    with _lock:
        return _get_layout_container(layout_id).layout_config


def set_layout(layout_id: str, layout: LayoutConfig) -> None:
    """Set the layout to the given layout id."""
    with _lock:
        container = _get_layout_container(layout_id)
        container.layout_config = layout
        write_layout_config(layout_id, layout)


def reset_layout(layout_id: str) -> None:
    """Reset the layout to its default configuration."""
    with _lock:
        container = _get_layout_container(layout_id)
        default_layout = container.default_config
        container.layout_config = default_layout
        write_layout_config(layout_id, default_layout)


def read_layout_config(layout_id: str, default_layout: LayoutConfig) -> LayoutConfig:
    """Read the saved configuration for the given layout."""
    # TODO: read the config and return
    return default_layout


def write_layout_config(layout_id: str, layout_config: LayoutConfig) -> None:
    """Overwrite the saved configuration for the given layout."""
    # TODO: write the config
    pass
