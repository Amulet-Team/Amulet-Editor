from __future__ import annotations

from PySide6.QtCore import Qt

from amulet_editor.models.plugin._plugin import PrivatePlugin

from .settings import SettingsPage


class SettingsPlugin(PrivatePlugin):
    _windows: list

    def enable(self):
        self._windows = []
        self.window.private_add_button("amulet_team:settings", "settings.svg", "Settings", self._on_click)

    def _on_click(self):
        settings = SettingsPage()
        settings.setWindowModality(Qt.ApplicationModal)
        settings.showNormal()
        self._windows.append(settings)
