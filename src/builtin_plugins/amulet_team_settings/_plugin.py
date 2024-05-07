from __future__ import annotations

from PySide6.QtCore import Qt

from amulet_editor.models.plugin import PluginV1
import tablericons

from .settings import SettingsPage

from amulet_team_main_window.api import add_static_toolbar_button


_windows: list = []


def load_plugin() -> None:
    add_static_toolbar_button(
        "amulet_team:settings", tablericons.settings, "Settings", _on_click
    )


def _on_click(self) -> None:
    settings = SettingsPage()
    settings.setWindowModality(Qt.WindowModality.ApplicationModal)
    settings.showNormal()
    self._windows.append(settings)


plugin = PluginV1(load_plugin)
