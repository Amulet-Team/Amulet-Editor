from __future__ import annotations

from PySide6.QtCore import Qt

from .settings import SettingsPage

from amulet_team_main_window.api import add_static_toolbar_button


_windows: list = []


def load_plugin():
    add_static_toolbar_button(
        "amulet_team:settings", "settings.svg", "Settings", _on_click
    )


def _on_click(self):
    settings = SettingsPage()
    settings.setWindowModality(Qt.WindowModality.ApplicationModal)
    settings.showNormal()
    self._windows.append(settings)
