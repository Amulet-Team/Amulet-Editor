"""A module to manage adding buttons to the toolbar.
To add layout buttons to the toolbar see the _layout module."""

from ._main_window import get_main_window
from ._main_window import ButtonProxy


def add_static_button() -> ButtonProxy:
    """
    Add an icon to the toolbar.

    :return: A ButtonProxy instance through which the button attributes can be set.
        You must store this somewhere in your plugin.
    """
    button = get_main_window().toolbar.add_static_button()
    return ButtonProxy(button)
