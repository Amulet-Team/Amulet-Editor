from __future__ import annotations
from typing import Type, Callable, Optional, Union
from uuid import uuid4
from threading import Lock
from weakref import ref
from inspect import isclass
import traceback

from PySide6.QtGui import QShortcut
from PySide6.QtCore import Qt

from amulet_editor.models.widgets.traceback_dialog import display_exception

from .main_window import Ui_AmuletMainWindow

# from ._view import ViewContainer, View

from amulet_team_inspector import show_inspector

from amulet_team_main_window2._application.widget import Widget, is_registered_widget
from amulet_team_main_window2._application.windows.window_proxy import (
    AbstractWindowProxy,
)
from amulet_team_main_window2._application.windows.layout import Layout
from amulet_team_main_window2._application.windows.tab_engine_imp import (
    StackedTabWidget,
)


# Terminology
# A Widget is an atomic GUI element within the program
# A Layout is an arrangement of widgets
# A tool button is a button in the toolbar. It can be configured to activate a layout or just run some code.

# A layout system.
#   controls where widgets are
#   Layout configurations are associated with identifiers
#   Layouts can be switched with code
# code can switch


UID = UUID = str


class AmuletMainWindow(Ui_AmuletMainWindow):
    # Class variables
    _lock = Lock()
    _instance: Optional[AmuletMainWindow] = None

    # Instance variables
    proxy: AmuletMainWindowProxy

    @classmethod
    def instance(cls) -> AmuletMainWindow:
        """
        Get the main window.
        Create it if it does not exist.
        The first call should show it.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = AmuletMainWindow()
            return cls._instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy = AmuletMainWindowProxy(self)

        # self._view_classes: dict[Type[View], UUID] = {}
        # self._view_containers: list[ViewContainer] = [self._view_container]
        # self._active_view = self._view_container
        f12 = QShortcut(Qt.Key.Key_F12, self)
        f12.activated.connect(show_inspector)

    # def activate_view(self, view_cls: Type[View]):
    #     """
    #     Enable a view registered to the given identifier.
    #     If a view of this type already exists it will be activated otherwise a new view will be created in the active container.
    #
    #     :param view_cls: The view type to enable
    #     """
    #     if view_cls not in self._view_classes:
    #         raise ValueError(f"View type {view_cls} has not been registered")
    #
    #     # Scan the view containers to see if a view of this type already exists
    #     for existing_view in self._view_containers:
    #         if existing_view.view_cls is view_cls:
    #             break
    #     else:
    #         existing_view = None
    #
    #     if existing_view is None:
    #         # Replace the active view
    #         view = view_cls()
    #         old_view = self._view_container.swap_view(view)
    #         # TODO: implement view caching
    #         if old_view is not None:
    #             old_view.deleteLater()
    #     else:
    #         existing_view.get_view().activate_view()
    #
    #     self._toolbar.activate(self._view_classes[view_cls])


class AmuletMainWindowProxy(AbstractWindowProxy):
    def __init__(self, window: AmuletMainWindow):
        self.__window = ref(window)

    def set_layout(self, layout: Union[Type[Widget], Layout]):
        """Configure the layout as requested"""
        window: AmuletMainWindow = self.__window()
        if window is None:
            raise RuntimeError
        if isinstance(layout, Layout):
            raise NotImplementedError
        elif isclass(layout) and issubclass(layout, Widget):
            if not is_registered_widget(layout):
                raise RuntimeError(f"Widget {layout} has not been registered.")
            for index in range(window.view_container.count() - 1, -1, -1):
                widget = window.view_container.widget(index)
                widget.hide()
                widget.deleteLater()
            try:
                widget = layout()
            except Exception as e:
                display_exception(
                    title=f"Error initialising Widget {layout}",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            else:
                tab_widget = StackedTabWidget()
                tab_widget.add_page(widget)
                window.view_container.insertWidget(0, tab_widget)
        else:
            raise RuntimeError


def get_main_window() -> AmuletMainWindowProxy:
    return AmuletMainWindow.instance().proxy


def _bind_callback_to_window(
    callback: Callable[[AmuletMainWindowProxy], None], window: AmuletMainWindow
) -> Callable[[], None]:
    return lambda: callback(window.proxy)


def add_toolbar_button(
    uid: UID,
    icon: str,
    name: str,
    callback: Callable[[AmuletMainWindowProxy], None] = None,
):
    """
    Add an icon to the toolbar for all windows.

    :param uid: The unique identifier of the button. Eg: author_name:button_name
    :param icon: The icon path to use in the toolbar.
    :param name: The name of the view to use in the icon tooltip.
    :param callback: The function to call when the button is clicked.
    :return:
    """
    window = AmuletMainWindow.instance()
    window.toolbar.add_dynamic_button(
        uid, icon, name, _bind_callback_to_window(callback, window)
    )


def add_static_toolbar_button(
    uid: UID,
    icon: str,
    name: str,
    callback: Callable[[AmuletMainWindowProxy], None] = None,
):
    """
    Add a static icon to the toolbar for all windows.
    These should be reserved for special cases.
    Third party plugins should use :func:`add_toolbar_button`.

    :param uid: The unique identifier of the button. Eg: author_name:button_name
    :param icon: The icon path to use in the toolbar.
    :param name: The name of the view to use in the icon tooltip.
    :param callback: The function to call when the button is clicked.
    :return:
    """
    window = AmuletMainWindow.instance()
    window.toolbar.add_static_button(
        uid, icon, name, _bind_callback_to_window(callback, window)
    )


def remove_toolbar_button(uid: UID):
    """
    Remove a toolbar button from all windows.

    :param uid: The unique identifier for the toolbar button to remove.
    :return:
    """
    window = AmuletMainWindow.instance()
    window.toolbar.remove_toolbar_button(uid)
