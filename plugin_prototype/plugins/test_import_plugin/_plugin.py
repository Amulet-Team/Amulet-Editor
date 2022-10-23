from __future__ import annotations
from contextlib import contextmanager
import logging

from amulet_editor_plugin_test.plugin import Plugin

log = logging.getLogger(__name__)


@contextmanager
def import_test():
    try:
        yield
    except ImportError:
        pass
    else:
        raise Exception("This should not happen")


with import_test():
    from amulet_team_editor.module_test import module_noop

with import_test():
    from amulet_team_editor import Plugin as EditorPlugin

with import_test():
    from my_name_my_plugin1 import Plugin as MyPlugin1


class TestPlugin(Plugin):
    def on_load(self):
        log.info("Test Import Plugin Loaded")

    def on_unload(self):
        log.info("Test Import Plugin Unloaded")
