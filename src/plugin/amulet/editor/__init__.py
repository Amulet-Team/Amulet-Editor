# Public functions and classes
from .widget import register_tab_widget, unregister_tab_widget, TabWidget
from .window import ButtonProxy
from .layout import (
    SplitterConfig,
    WidgetConfig,
    WidgetStackConfig,
    WindowConfig,
    LayoutConfig,
    register_layout,
    activate_layout,
    active_layout,
    create_layout_button,
)
from ._signal import init_editor, destroy_editor
from . import _command
