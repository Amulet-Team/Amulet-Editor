from amulet_editor_plugin_test.plugin import Plugin

from .module_test import module_noop as relative_module_noop
from .package_test import package_noop as relative_package_noop, submodule_noop as relative_package_submodule_noop
from .package_test.submodule_test import submodule_noop as relative_submodule_noop

print("a1", relative_module_noop())
print("a2", relative_package_noop())
print("a3", relative_package_submodule_noop())
print("a4", relative_submodule_noop())

from amulet_team.editor.module_test import module_noop as absolute_module_noop
from amulet_team.editor.package_test import package_noop as absolute_package_noop, submodule_noop as absolute_package_submodule_noop
from amulet_team.editor.package_test.submodule_test import submodule_noop as absolute_submodule_noop

print("a5", absolute_module_noop())
print("a6", absolute_package_noop())
print("a7", absolute_package_submodule_noop())
print("a8", absolute_submodule_noop())


class EditorPlugin(Plugin):
    def on_load(self):
        print("Editor Plugin Loaded")

    def on_unload(self):
        print("Editor Plugin Unloaded")

    def custom_method(self, text: str):
        print(f"Custom {text} method")
