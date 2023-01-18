from __future__ import annotations

from amulet_editor.models.plugin._plugin import Plugin

from .home import HomeView

from amulet_team_main_window import MainWindowPluginAPI


class HomePagePlugin(Plugin):
    def on_start(self):
        main_window_plugin = self.get_plugin(MainWindowPluginAPI)
        main_window_plugin.register_view(
            "amulet_team:home", "home.svg", "Home", HomeView
        )
