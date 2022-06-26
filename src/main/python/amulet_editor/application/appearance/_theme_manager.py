import os

from amulet_editor.data import build, project
from amulet_editor.application.appearance._theme import Theme
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):

    changed = Signal(object)

    def __init__(self) -> None:
        super().__init__(parent=None)

        self._themes: list[Theme] = []
        theme_dir = build.get_resource("themes")
        for theme in os.listdir(theme_dir):
            if theme != "_default":
                self._themes.append(Theme(os.path.join(theme_dir, theme)))

        self.set_theme(project.settings()["theme"])

    def list_themes(self) -> list[str]:
        return [theme.name for theme in self._themes]

    def set_theme(self, theme_name: str) -> None:
        for theme in self._themes:
            if theme.name == theme_name:
                self.theme = theme
                self.changed.emit(self.theme)
                return


theme_manager = ThemeManager()

changed = theme_manager.changed


def list_themes() -> list[str]:
    return theme_manager.list_themes()


def set_theme(theme_name: str) -> None:
    return theme_manager.set_theme(theme_name)


def theme() -> Theme:
    return theme_manager.theme
