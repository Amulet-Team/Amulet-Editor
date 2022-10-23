from amulet_editor_plugin_test.plugin import Plugin


class MyPlugin(Plugin):
    def on_load(self):
        print("Third Party Plugin Loaded")
        editor: EditorPlugin = self.get_plugin("amulet_team.editor")
        editor.custom_method("test")

    def on_unload(self):
        print("Plugin Unloaded")
