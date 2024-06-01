from ._plugin import plugin  # Private plugin initialisation

# Public functions and classes
from ._tab_engine import TabWidget
from ._layout import (
    SplitterConfig,
    WidgetConfig,
    WidgetStackConfig,
    WindowConfig,
    LayoutConfig,
    register_layout,
    unregister_layout,
    activate_layout,
    active_layout,
    create_layout_button,
)
from ._widget import register_widget, unregister_widget
from ._main_window.toolbar import ButtonProxy
