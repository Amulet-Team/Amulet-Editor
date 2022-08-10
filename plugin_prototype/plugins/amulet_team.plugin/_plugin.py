from amulet_editor_plugin_test.plugin import Plugin


class EditorPlugin(Plugin):
    def on_load(self):
        print("Plugin Loaded")
        editor = self.get_plugin("amulet_team.editor")
        editor.custom_method("test")

    def on_unload(self):
        print("Plugin Unloaded")
