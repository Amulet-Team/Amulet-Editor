from ._plugin import plugin  # Private plugin initialisation

# Public functions and classes
from .widget import register_widget, unregister_widget
from .window import (
    ButtonProxy,
    TabWidget,
)
from .layout import (
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
from ._signal import init_editor, destroy_editor
