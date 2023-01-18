from typing import Type, Callable

from amulet_team_main_window.models.view import View
from amulet_team_main_window import _plugin


UID = str


def activate_view(view_uid: UID):
    _plugin.window.activate_view(view_uid)


def register_view(uid: UID, icon: str, name: str, view: Type[View]):
    _plugin.window.register_view(uid, icon, name, view)


def add_button(uid: UID, icon: str, name: str, callback: Callable[[], None] = None):
    _plugin.window.add_button(uid, icon, name, callback)


def add_static_button(
    uid: UID, icon: str, name: str, callback: Callable[[], None] = None
):
    _plugin.window.add_static_button(uid, icon, name, callback)
