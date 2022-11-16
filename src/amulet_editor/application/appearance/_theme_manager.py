import os
import glob
import logging

from amulet_editor.application.appearance._theme import Theme
from amulet_editor.data import build, project
from amulet_editor.data.project._settings import DefaultTheme
from PySide6.QtCore import QObject, Signal

log = logging.getLogger(__name__)


class ThemeManager(QObject):

    changed = Signal(object)

    def __init__(self) -> None:
        super().__init__(parent=None)

        self._themes: list[Theme] = []
        self.theme = None
        theme_dir = build.get_resource("themes")
        for theme_json_path in glob.glob(os.path.join(theme_dir, "*", "theme.json")):
            theme_path = os.path.dirname(theme_json_path)
            try:
                self._themes.append(Theme(theme_path))
            except Exception as e:
                log.exception(f"Failed to load theme in {theme_path}", exc_info=e)
        if not self._themes:
            raise RuntimeError("Did not load any themes.")
        self.set_theme(project.settings()["theme"])
        if self.theme is None:
            self.set_theme(DefaultTheme)
            if self.theme is None:
                raise RuntimeError("Could not load default theme.")

    def list_themes(self) -> list[str]:
        return [theme.name for theme in self._themes]

    def set_theme(self, theme_name: str):
        """
        Try and set the requested theme.
        If no matching theme exists then do nothing.
        """
        theme_ = next((t for t in self._themes if t.name == theme_name), None)
        if theme_ is not None:
            self.theme = theme_
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
