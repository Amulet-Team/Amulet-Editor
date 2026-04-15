"""A module to manage everything about layouts.
Registering layouts, adding layout buttons and enabling layouts"""

from __future__ import annotations
from typing import Callable, cast
from threading import Lock, current_thread, main_thread
from dataclasses import dataclass
import re
from weakref import ref

from PySide6.QtCore import Qt, QPoint, QSize, QObject

from plugin.amulet.editor._toolbar_button import ToolbarButton

from plugin.amulet.editor.widget import _missing
from plugin.amulet.editor.widget import _widget
from plugin.amulet.editor.window import _tab_widget
from plugin.amulet.editor.window import _main_window
from plugin.amulet.editor.window import _child_window

# my_namespace.my_layout
# my_namespace.my_group.my_layout
LayoutIdPattern = re.compile(r"[a-z0-9_]+\.[a-z0-9_.]+")


# TODO: what should this be?
#  This needs to be picklable
#  The contained data must not depend on the plugin because it may not be active when it is unpickled.
#  It must contain enough info to reconstruct the layout and contained widgets
#  Layout can be a custom object containing division weightings, orientation and contained widgets.
#  Widgets can be the qualified name to the widget and some metadata to reconstruct them.
#   Should widgets have a method to dump the metadata and a class method to reconstruct them with the metadata?
#   If the plugin does not get enabled, the widget will be a missing widget.


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


@dataclass(frozen=True)
class HiddenLayout:
    """Storage for layout UI elements when not active."""

    main_window_splitter: _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter
    sub_windows: tuple[_child_window.AmuletChildWindow, ...]


@dataclass
class LayoutContainer:
    layout_id: str
    default_config: LayoutConfig
    layout_config: LayoutConfig
    button_ref: Callable[[], ToolbarButton | None] = cast(
        Callable[[], ToolbarButton | None], lambda: None
    )
    hidden_layout: HiddenLayout | None = None


# The lock must be acquired before reading/writing the objects below.
lock = Lock()
# The layouts that have been registered
layouts = dict[str, LayoutContainer]()
# The id for the currently active layout
_active_layout: LayoutContainer | None = None


def _get_layout_container(layout_id: str) -> LayoutContainer:
    """Get the layout container for the given layout id.

    The lock must be acquired before calling this.

    :param layout_id: The layout id to get.
    :raises ValueError: If the layout has not been registered.
    :return:
    """
    layout_container = layouts.get(layout_id, None)
    if layout_container is None:
        raise ValueError(f"No registered layout for id {layout_id}")
    return layout_container


def register_layout(layout_id: str, layout: LayoutConfig) -> None:
    """Register a new layout.

    This must be called before a layout can be activated.

    :param layout_id: The unique identifier for the layout.
        The unique id must contain a namespace and layout name separated by "."
        It may contain other names separated by "."
        Names must only contain lower case a-z, 0-9 and _ characters.
        Eg "my_namespace.my_layout" or "my_namespace.my_group.my_layout"
        This won't be shown to the user but can be used by other plugins to enable the layout.
    :param layout: The default layout to use.
        If the user has made changes to the layout, the changes will be displayed.
    """
    if LayoutIdPattern.fullmatch(layout_id) is None:
        raise ValueError(f"Invalid identifier {layout_id}")
    with lock:
        if layout_id in layouts:
            raise ValueError(f"Layout id {layout_id} has already been registered.")
        layout_container = LayoutContainer(layout_id, layout, layout)
        layouts[layout_id] = layout_container


def unregister_layout(layout_id: str) -> None:
    """Unregister the layout.

    When the plugin is unloaded, it must unregister all layouts that it registered.
    If a button was created it must be destroyed before calling this.

    :param layout_id: The unique identifier for the layout.
    :return:
    """
    with lock:
        if layout_id not in layouts:
            raise ValueError(f"Layout id {layout_id} does not exist.")
        del layouts[layout_id]


def active_layout() -> LayoutContainer | None:
    """Get the unique id for the currently active layout."""
    return _active_layout


def activate_layout(layout_id: str) -> None:
    """Activate the layout.

    If the layout has a button, this just clicks the button, otherwise emulates the click.

    The layout must have been previously registered.

    :param layout_id: The unique identifier for the layout.
    :return:
    """
    with lock:
        layout_container = _get_layout_container(layout_id)
        button = layout_container.button_ref()
        if button is not None:
            # If the layout has an associated button, click it.
            button.click()
        else:
            # If there is no associated button then manually enable it.
            _main_window.get_main_window()._toolbar.uncheck_layout_buttons()
            _setup_layout(layout_container)


def create_layout_button(layout_id: str) -> _main_window.ButtonProxy:
    """Create a button that will activate the specified layout.

    The layout must be registered before calling this.

    :param layout_id: The layout id for the layout that will be activated when clicked.
    """
    with lock:
        layout_container = _get_layout_container(layout_id)
        if layout_container.button_ref() is not None:
            raise ValueError(f"A layout button for id {layout_id} already exists.")
        button = _main_window.get_main_window()._toolbar.add_layout_button()
        button.clicked.connect(lambda: _setup_layout(layout_container))
        layout_container.button_ref = ref(button)
        # TODO: set up the button
        #  Context menu:
        #   Reset to default layout
        #   Delete button
        #   Save layout

        return _main_window.ButtonProxy(button)


def _populate_widgets_of_type(
    tab_widget: QObject,
    widget_identifier: str,
    widget_cls: type[_widget.TabWidget],
) -> None:
    if isinstance(tab_widget, _tab_widget.TabWidgetStack):
        for tab_widget_meta in tab_widget._get_tab_widgets():
            # If it is a missing widget
            if tab_widget_meta.identifier == _missing.MissingTabIdentifier:
                widget = tab_widget_meta.widget
                if (
                    isinstance(widget, _missing.MissingWidget)
                    and widget.identifier == widget_identifier
                ):
                    # Replace the placeholder with the real widget
                    tab_widget._replace_widget(
                        tab_widget_meta,
                        _tab_widget.TabWidgetMeta(widget_identifier, widget_cls()),
                    )
                    tab_widget_meta.tab.deleteLater()
                    tab_widget_meta.widget.deleteLater()
    elif isinstance(tab_widget, _tab_widget.RecursiveSplitter):
        for child_tab_widget in tab_widget.children():
            _populate_widgets_of_type(child_tab_widget, widget_identifier, widget_cls)


def populate_widgets(
    widget_identifier: str, widget_cls: type[_widget.TabWidget]
) -> None:
    """Populate all missing widgets of this type.

    If a widget is created before its plugin is loaded it will be a missing widget.
    This function replaces all missing widgets with the real widget."""
    assert (
        current_thread() is main_thread()
    ), "This can only be called from the main thread."
    _populate_widgets_of_type(
        _main_window.get_main_window()._widget, widget_identifier, widget_cls
    )
    for sub_window in _child_window.sub_windows:
        _populate_widgets_of_type(sub_window._widget, widget_identifier, widget_cls)


def _remove_widgets_of_type(tab_widget: QObject, widget_identifier: str) -> None:
    if isinstance(tab_widget, _tab_widget.TabWidgetStack):
        for tab_widget_meta in tab_widget._get_tab_widgets():
            if tab_widget_meta.identifier == widget_identifier:
                tab_widget._replace_widget(
                    tab_widget_meta,
                    _tab_widget.TabWidgetMeta(
                        widget_identifier, _missing.MissingWidget(widget_identifier)
                    ),
                )
                tab_widget_meta.tab.deleteLater()
                tab_widget_meta.widget.deleteLater()
    elif isinstance(tab_widget, _tab_widget.RecursiveSplitter):
        for child_tab_widget in tab_widget.children():
            _remove_widgets_of_type(child_tab_widget, widget_identifier)


def remove_widgets(widget_identifier: str) -> None:
    """Remove all widgets of this type and replace with a missing widget."""
    for layout in layouts.values():
        hidden_layout = layout.hidden_layout
        if hidden_layout is not None:
            _remove_widgets_of_type(
                hidden_layout.main_window_splitter, widget_identifier
            )
            for sub_window in hidden_layout.sub_windows:
                _remove_widgets_of_type(sub_window._widget, widget_identifier)
    _remove_widgets_of_type(_main_window.get_main_window()._widget, widget_identifier)


def _init_layout(
    layout: SplitterConfig | WidgetStackConfig,
) -> _tab_widget.TabWidgetStack | _tab_widget.RecursiveSplitter:
    if isinstance(layout, SplitterConfig):
        splitter_widget = _tab_widget.RecursiveSplitter()
        splitter_widget.setOrientation(layout.orientation)
        splitter_widget.addWidget(_init_layout(layout.first))
        splitter_widget.addWidget(_init_layout(layout.second))
        left_weight = max(1, min(100, int(100 * layout.weight)))
        right_weight = 100 - left_weight
        splitter_widget.setStretchFactor(0, left_weight)
        splitter_widget.setStretchFactor(1, right_weight)
        return splitter_widget
    elif isinstance(layout, WidgetStackConfig):
        tab_widget = _tab_widget.TabWidgetStack()
        for widget_config in layout.widgets:
            try:
                widget_cls = _widget.get_tab_widget_cls(widget_config.identifier)
            except KeyError:
                tab_widget_meta = _tab_widget.TabWidgetMeta(
                    _missing.MissingTabIdentifier,
                    _missing.MissingWidget(widget_config.identifier),
                )
            else:
                tab_widget_meta = _tab_widget.TabWidgetMeta(
                    widget_config.identifier, widget_cls()
                )

            tab_widget._add_tab_widget(tab_widget_meta)
        return tab_widget
    else:
        raise RuntimeError(f"Unknown layout type {type(layout)}")


def _create_layout(layout_container: LayoutContainer) -> None:
    """Initialisation of the layout."""
    layout_config = layout_container.layout_config
    # TODO: set window position and size
    _main_window.get_main_window()._replace_widget(
        _init_layout(layout_config.main_window.layout)
    ).deleteLater()
    for config in layout_config.sub_windows:
        _child_window.create_sub_window(
            _init_layout(config.layout),
        )


def _destroy_layout() -> None:
    """Destroy the existing layout.
    This is used when resetting the active layout."""
    for sub_window in _child_window.sub_windows:
        sub_window.close()
    widget = _main_window.get_main_window()._replace_widget(
        _tab_widget.RecursiveSplitter()
    )
    widget.hide()
    widget.deleteLater()


def _setup_layout(new_layout_container: LayoutContainer) -> None:
    """Tear down the existing widgets and populate the new layout."""
    global _active_layout
    assert (
        current_thread() is main_thread()
    ), "This can only be called from the main thread."

    old_layout_container = active_layout()

    if old_layout_container is new_layout_container:
        # If the layout is already active then do nothing.
        return

    old_sub_windows = []
    if old_layout_container is not None:
        # Pull down all the old sub-windows
        old_sub_windows = list(_child_window.sub_windows)
        _child_window.sub_windows.clear()
        for sub_window in old_sub_windows:
            sub_window.hide()

    main_window = _main_window.get_main_window()
    hidden_layout = new_layout_container.hidden_layout
    if hidden_layout is None:
        # Layout was not active before
        # Create from scratch
        old_main_view_container = main_window._replace_widget(
            _tab_widget.RecursiveSplitter()
        )
        _create_layout(new_layout_container)
    else:
        new_main_view_container = hidden_layout.main_window_splitter
        old_main_view_container = main_window._replace_widget(new_main_view_container)
        new_main_view_container.show()
        for sub_window in hidden_layout.sub_windows:
            sub_window.show()
        _child_window.sub_windows.update(hidden_layout.sub_windows)
        new_layout_container.hidden_layout = None
    # Without this the last shown sub-window will be active.
    main_window.activateWindow()

    if old_layout_container is None:
        old_main_view_container.deleteLater()
    else:
        old_main_view_container.hide()
        old_layout_container.hidden_layout = HiddenLayout(
            old_main_view_container, tuple(old_sub_windows)
        )

    _active_layout = new_layout_container


def _get_layout_config() -> LayoutConfig:
    """Get the current layout configuration."""
    raise NotImplementedError


def save_layout_config() -> None:
    """Save the layout configuration for the active layout."""
    with lock:
        layout_container = active_layout()
        if layout_container is None:
            return
        layout_container.layout_config = _get_layout_config()
        # TODO: save config file.


def reset_layout_config(layout_id: str) -> None:
    """Reset the layout to its default configuration.
    If the layout is active this will update the display.
    """
    assert (
        current_thread() is main_thread()
    ), "This can only be called from the main thread."
    with lock:
        layout_container = _get_layout_container(layout_id)
        layout_container.layout_config = layout_container.default_config
        # TODO: delete config file.
        if active_layout() is layout_container:
            _destroy_layout()
            _create_layout(layout_container)
