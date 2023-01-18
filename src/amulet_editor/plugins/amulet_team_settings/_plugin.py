from __future__ import annotations

from PySide6.QtCore import Qt

from amulet_editor.models.plugin._plugin import Plugin

from .settings import SettingsPage

from amulet_team_main_window import MainWindowPluginAPI


class SettingsPlugin(Plugin):
    _windows: list

    def on_start(self):
        self._windows = []
        main_window_plugin = self.get_plugin(MainWindowPluginAPI)
        main_window_plugin.add_static_button(
            "amulet_team:settings", "settings.svg", "Settings", self._on_click
        )

    def _on_click(self):
        settings = SettingsPage()
        settings.setWindowModality(Qt.ApplicationModal)
        settings.showNormal()
        self._windows.append(settings)
