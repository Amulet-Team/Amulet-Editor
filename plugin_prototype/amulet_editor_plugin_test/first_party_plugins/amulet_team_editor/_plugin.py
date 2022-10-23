import logging

from amulet_editor_plugin_test.plugin import Plugin

from .module_test import module_noop as relative_module_noop
from .package_test import package_noop as relative_package_noop, submodule_noop as relative_package_submodule_noop
from .package_test.submodule_test import submodule_noop as relative_submodule_noop
from amulet_team_editor.module_test import module_noop as absolute_module_noop
from amulet_team_editor.package_test import package_noop as absolute_package_noop, submodule_noop as absolute_package_submodule_noop
from amulet_team_editor.package_test.submodule_test import submodule_noop as absolute_submodule_noop

log = logging.getLogger(__name__)

log.info("a1", relative_module_noop())
log.info("a2", relative_package_noop())
log.info("a3", relative_package_submodule_noop())
log.info("a4", relative_submodule_noop())
log.info("a5", absolute_module_noop())
log.info("a6", absolute_package_noop())
log.info("a7", absolute_package_submodule_noop())
log.info("a8", absolute_submodule_noop())


class EditorPlugin(Plugin):
    def on_load(self):
        log.info("Editor Plugin Loaded")

    def on_unload(self):
        log.info("Editor Plugin Unloaded")

    def custom_method(self, text: str):
        log.info(f"Custom {text} method")
