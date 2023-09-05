from typing import Type
from .tab_engine import TabPage


class Widget(TabPage):
    def activate_view(self):
        """
        Run every time the view is activated by code or by clicking the tool button associated with the view.
        This is useful if the view wants to reset to a default state every time the tool button is clicked.
        """
        pass

    def can_disable_view(self) -> bool:
        """
        Can the view be disabled.
        Return False if for some reason the view cannot be disabled.

        :return: True if the view can be disabled. False otherwise.
        """
        return True

    def disable_view(self):
        """
        This is run when a view is about to be removed from a view container.
        This gives the view a chance to do any cleaning up before it is removed and potentially destroyed.
        This method must leave the view in a state where it can be destroyed or activated again.
        """
        pass


_widget_classes: set[Type[Widget]] = set()


def is_registered_widget(widget_cls: Type[Widget]):
    return widget_cls in _widget_classes


def register_widget(widget_cls: Type[Widget]):
    """
    Register a widget class.

    :param widget_cls: The widget class to register.
    """
    if not issubclass(widget_cls, Widget) or widget_cls is Widget:
        raise TypeError("widget must be a subclass of Widget")
    if widget_cls in _widget_classes:
        raise ValueError(f"Widget type {widget_cls} has already been registered.")
    _widget_classes.add(widget_cls)
    # TODO: find out if any filler widgets want to be this widget


def unregister_widget(widget_cls: Type[Widget]):
    """
    Unregister a widget.

    :param widget_cls: The widget class to unregister.
    :return:
    """
    # TODO: raise NotImplementedError
    pass
