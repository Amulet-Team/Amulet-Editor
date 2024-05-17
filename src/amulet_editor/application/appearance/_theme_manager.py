import os
from typing import Optional

from amulet_editor.application.appearance._theme import AbstractBaseTheme, LegacyTheme
from amulet_editor.resources import get_resource
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    changed = Signal(object)

    def __init__(self) -> None:
        super().__init__(parent=None)
        self._theme: Optional[AbstractBaseTheme] = None

        self._themes: list[AbstractBaseTheme] = []
        theme_dir = get_resource("themes")
        for theme_ in os.listdir(theme_dir):
            if theme_ != "_default":
                self._themes.append(LegacyTheme(os.path.join(theme_dir, theme_)))
        self.set_theme("Amulet Dark")

    @property
    def theme(self) -> AbstractBaseTheme:
        assert self._theme is not None
        return self._theme

    def list_themes(self) -> list[str]:
        return [theme_.name for theme_ in self._themes]

    def set_theme(self, theme_name: str) -> None:
        for theme_ in self._themes:
            if theme_.name == theme_name:
                self._theme = theme_
                self.changed.emit(self.theme)
                break


theme_manager = ThemeManager()

changed = theme_manager.changed


def list_themes() -> list[str]:
    return theme_manager.list_themes()


def set_theme(theme_name: str) -> None:
    theme_manager.set_theme(theme_name)


def theme() -> AbstractBaseTheme:
    return theme_manager.theme
