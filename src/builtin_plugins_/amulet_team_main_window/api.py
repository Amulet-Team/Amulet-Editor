from typing import Type, Callable

from amulet_team_main_window import _plugin
from .models.view import View
from .application.windows.main_window import AmuletMainWindow


UID = str


def get_windows() -> tuple[AmuletMainWindow, ...]:
    return (get_active_window(),)


def get_active_window() -> AmuletMainWindow:
    assert _plugin.window is not None
    return _plugin.window


def register_view(view_cls: Type[View], icon: str, name: str) -> None:
    for window in get_windows():
        window.register_view(view_cls, icon, name)


def unregister_view(view_cls: Type[View]) -> None:
    for window in get_windows():
        window.unregister_view(view_cls)


def add_toolbar_button(
    uid: UID, icon_path: str, name: str, callback: Callable[[], None] = lambda: None
) -> None:
    """
    Add an icon to the toolbar for all windows.

    :param uid: The unique identifier of the button. Eg: author_name:button_name
    :param icon_path: The path to an SVG image the button should use.
    :param name: The name of the view to use in the icon tooltip.
    :param callback: The function to call when the button is clicked.
    :return:
    """
    for window in get_windows():
        window.add_toolbar_button(uid, icon_path, name, callback)


def add_static_toolbar_button(
    uid: UID, icon_path: str, name: str, callback: Callable[[], None] = lambda: None
) -> None:
    """
    Add a static icon to the toolbar for all windows.
    These should be reserved for special cases.
    Third party plugins should use :func:`add_button`.

    :param uid: The unique identifier of the button. Eg: author_name:button_name
    :param icon_path: The path to an SVG image the button should use.
    :param name: The name of the view to use in the icon tooltip.
    :param callback: The function to call when the button is clicked.
    :return:
    """
    for window in get_windows():
        window.add_static_toolbar_button(uid, icon_path, name, callback)


def remove_toolbar_button(uid: UID) -> None:
    """
    Remove a toolbar button from all windows.

    :param uid: The unique identifier for the toolbar button to remove.
    :return:
    """
    for window in get_windows():
        window.remove_toolbar_button(uid)
