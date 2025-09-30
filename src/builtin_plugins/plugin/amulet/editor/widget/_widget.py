"""A module to manage widget class registration and access."""

from threading import Lock

from plugin.amulet.editor.layout import _layout
from .abc import TabWidget

# Maps the classes qualified name to the class.
lock = Lock()
_widget_classes: dict[str, type[TabWidget]] = {}


def register_tab_widget(widget_identifier: str, widget_cls: type[TabWidget]) -> None:
    """
    Register a widget class.

    :param widget_identifier: The identifier for this widget type. Eg my_namespace.my_plugin.MyWidget
    :param widget_cls: The widget class to register.
    """
    if not issubclass(widget_cls, TabWidget):
        raise TypeError("widget_cls must be a subclass of TabWidget")
    with lock:
        if widget_identifier in _widget_classes:
            raise ValueError(
                f"TabWidget type {widget_identifier} has already been registered."
            )
        _widget_classes[widget_identifier] = widget_cls
        _layout.populate_widgets(widget_identifier, widget_cls)


def unregister_tab_widget(widget_identifier: str) -> None:
    """
    Unregister a widget class.

    :param widget_identifier: The identifier for the widget type. Eg my_namespace.my_plugin.MyWidget
    :return:
    """
    with lock:
        if widget_identifier not in _widget_classes:
            raise ValueError(
                f"TabWidget type {widget_identifier} has not been registered."
            )
        del _widget_classes[widget_identifier]
        _layout.remove_widgets(widget_identifier)


def get_tab_widget_cls(widget_identifier: str) -> type[TabWidget]:
    """Get the registered widget from its qualified name.

    For internal use by this plugin only.

    :param widget_identifier: The identifier for this widget type. Eg my_namespace.my_plugin.MyWidget
    :raises KeyError: if the widget has not been registered yet.
    :return:
    """
    with lock:
        return _widget_classes[widget_identifier]
