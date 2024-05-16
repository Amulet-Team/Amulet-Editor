from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.settings._pages import SettingsPage
from amulet_editor.tools.settings._panels import SettingsPanel


class Settings(AmuletTool):
    def __init__(self):
        self._page = AmuletView(SettingsPage())
        self._primary_panel = AmuletView(SettingsPanel())
        self._secondary_panel = AmuletView(None)

    @property
    def page(self) -> AmuletView:
        return self._page

    @property
    def primary_panel(self) -> AmuletView:
        return self._primary_panel

    @property
    def secondary_panel(self) -> AmuletView:
        return self._secondary_panel

    @property
    def name(self) -> str:
        return "Settings"

    @property
    def icon_name(self) -> str:
        return "settings.svg"
