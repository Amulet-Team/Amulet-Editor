from __future__ import annotations
import logging
import time

from amulet_editor_plugin_test.plugin import Plugin

log = logging.getLogger(__name__)


class TestPlugin(Plugin):
    def on_load(self):
        time.sleep(5)
        log.info("Test Import Plugin Loaded")

    def on_unload(self):
        time.sleep(5)
        log.info("Test Import Plugin Unloaded")
