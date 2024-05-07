import os
from typing import Optional

from amulet_editor.application.appearance._theme import Theme
from amulet_editor.data import build, project
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    changed = Signal(object)

    def __init__(self):
        super().__init__(parent=None)
        self._theme: Optional[Theme] = None

        self._themes: list[Theme] = []
        theme_dir = build.get_resource("themes")
        for theme_ in os.listdir(theme_dir):
            if theme_ != "_default":
                self._themes.append(Theme(os.path.join(theme_dir, theme_)))

        self.set_theme(project.settings()["theme"])

    @property
    def theme(self) -> Theme:
        return self._theme

    def list_themes(self) -> list[str]:
        return [theme_.name for theme_ in self._themes]

    def set_theme(self, theme_name: str):
        for theme_ in self._themes:
            if theme_.name == theme_name:
                self._theme = theme_
                self.changed.emit(self.theme)
                return


theme_manager = ThemeManager()

changed = theme_manager.changed


def list_themes() -> list[str]:
    return theme_manager.list_themes()


def set_theme(theme_name: str):
    return theme_manager.set_theme(theme_name)


def theme() -> Theme:
    return theme_manager.theme
