from ._plugin import plugin  # Private plugin initialisation

# Public functions and classes
from ._tab_engine import TabWidget
from ._widget import register_widget, unregister_widget
from ._layout import create_layout_button
from ._main_window.toolbar import ButtonProxy
