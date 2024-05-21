"""A module to manage widget class registration and access."""
from threading import Lock

from ._tab_engine import TabWidget
from . import _layout as layout


# Maps the classes qualified name to the class.
lock = Lock()
_widget_classes: dict[str, type[TabWidget]] = {}


def is_registered_widget(widget_cls: type[TabWidget]) -> bool:
    with lock:
        return widget_cls.__qualname__ in _widget_classes


def register_widget(widget_cls: type[TabWidget]) -> None:
    """
    Register a widget class.

    :param widget_cls: The widget class to register.
    """
    with lock:
        if not issubclass(widget_cls, TabWidget):
            raise TypeError("widget must be a subclass of TabWidget")
        if widget_cls.__qualname__ in _widget_classes:
            raise ValueError(f"TabWidget type {widget_cls} has already been registered.")
        _widget_classes[widget_cls.__qualname__] = widget_cls
        layout.populate_widgets(widget_cls)


def unregister_widget(widget_cls: type[TabWidget]) -> None:
    """
    Unregister a widget.

    :param widget_cls: The widget class to unregister.
    :return:
    """
    qualname = widget_cls.__qualname__
    with lock:
        if qualname not in _widget_classes:
            raise ValueError(f"TabWidget type {widget_cls} has not been registered.")
        del _widget_classes[qualname]
        layout.remove_widgets(widget_cls)


def get_widget_cls(widget_qualname: str) -> type[TabWidget]:
    """Get the registered widget from its qualified name.

    For internal use by this plugin only.

    :param widget_qualname: The qualified name of the widget.
    :raises KeyError: if the widget has not been registered yet.
    :return:
    """
    with lock:
        return _widget_classes[widget_qualname]
