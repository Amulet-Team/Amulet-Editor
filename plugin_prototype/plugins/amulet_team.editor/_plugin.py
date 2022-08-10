from amulet_editor_plugin_test.plugin import Plugin

from ._module_test import noop

noop()
from ._package_test import noop

noop()
from amulet_team.editor._module_test import noop

noop()
from amulet_team.editor._package_test._submodule_test import noop

noop()


class EditorPlugin(Plugin):
    def on_load(self):
        print("Editor Plugin Loaded")

    def on_unload(self):
        print("Editor Plugin Unloaded")

    def custom_method(self, text: str):
        print(f"Custom {text} method")
