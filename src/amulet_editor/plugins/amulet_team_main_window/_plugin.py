from __future__ import annotations
from typing import Optional, Type, Callable

from amulet_editor.models.plugin import Plugin, PluginAPI
from amulet_team_main_window.application.windows.main_window import AmuletMainWindow, UID, View


class MainWindowPluginAPI(PluginAPI):
    # Instance attributes
    _plugin: MainWindowPlugin

    @property
    def View(self) -> Type[View]:
        return View

    def activate_view(self, view_uid: UID):
        self._plugin.window.activate_view(view_uid)

    def register_view(self, uid: UID, icon: str, name: str, view: Type[View]):
        self._plugin.window.register_view(uid, icon, name, view)

    def add_button(self, uid: UID, icon: str, name: str, callback: Callable[[], None] = None):
        self._plugin.window.add_button(uid, icon, name, callback)

    def add_static_button(self, uid: UID, icon: str, name: str, callback: Callable[[], None] = None):
        self._plugin.window.add_static_button(uid, icon, name, callback)


class MainWindowPlugin(Plugin):
    window: Optional[AmuletMainWindow]

    APIClass = MainWindowPluginAPI

    def on_init(self):
        self.window = None

    def on_start(self):
        self.window = AmuletMainWindow()
        self.window.showMaximized()
