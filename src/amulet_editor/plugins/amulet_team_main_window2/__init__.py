from ._plugin import plugin  # Private plugin initialisation

# Public functions and classes
from ._application.widget import Widget, register_widget, unregister_widget
from ._application.windows.window_proxy import AbstractWindowProxy
from ._application.windows.main_window import (
    AmuletMainWindowProxy,
    get_main_window,
    add_toolbar_button,
)
from ._application.windows.main_window.toolbar import ButtonProxy
