from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from amulet_editor_plugin_test.plugin import Plugin

log = logging.getLogger(__name__)


if TYPE_CHECKING:
    # If you want type checking in your IDE you can do this.
    # TYPE_CHECKING is False at runtime so this code will never get run, but it allows the IDE to know the API of the object.
    # Note: you should also have `from __future__ import annotations` as the first line in the file.
    from amulet_team_editor import Plugin as EditorPlugin


class MyPlugin(Plugin):
    def on_load(self):
        log.info("My Plugin1 Loaded")
        editor: EditorPlugin = self.get_plugin("amulet_team_editor")
        editor.custom_method("test")

    def on_unload(self):
        log.info("My Plugin1 Unloaded")
