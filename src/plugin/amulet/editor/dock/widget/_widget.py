"""A module to manage widget class registration and access."""

from threading import Lock
from collections.abc import Callable

from PySide6.QtCore import Signal, QObject

from amulet.level.abc import Level

from ._abc import DockWidget

type DockWidgetConstructor = Callable[[Level], DockWidget]


class DockWidgetAPI(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()
        self._widget_classes: dict[str, DockWidgetConstructor] = {}

    # Emitted when a widget is registered
    widget_registered = Signal(str)

    def register_tab_widget(
        self, widget_identifier: str, widget_constructor: DockWidgetConstructor
    ) -> None:
        """
        Register a widget class.

        :param widget_identifier: The identifier for this widget type. Eg my_namespace.my_plugin.MyWidget
        :param widget_constructor: The constructor for the widget class. This can be the class object if it has a default constructor.
        """

        with self._lock:
            if widget_identifier in self._widget_classes:
                raise ValueError(
                    f"TabWidget type {widget_identifier} has already been registered."
                )
            self._widget_classes[widget_identifier] = widget_constructor
            self.widget_registered.emit(widget_identifier)

    def get_tab_widget_constructor(
        self, widget_identifier: str
    ) -> DockWidgetConstructor:
        """Get the registered widget from its qualified name.

        For internal use by this plugin only.

        :param widget_identifier: The identifier for this widget type. Eg my_namespace.my_plugin.MyWidget
        :raises KeyError: if the widget has not been registered yet.
        :return:
        """
        with self._lock:
            return self._widget_classes[widget_identifier]


dock_widget_api = DockWidgetAPI()
widget_registered = dock_widget_api.widget_registered
register_tab_widget = dock_widget_api.register_tab_widget
get_tab_widget_constructor = dock_widget_api.get_tab_widget_constructor
