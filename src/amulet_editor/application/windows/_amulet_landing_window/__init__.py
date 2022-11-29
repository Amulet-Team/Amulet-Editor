from ._landing_window import Ui_AmuletLandingWindow
from PySide6.QtCore import Slot
from .pages.settings import SettingsPage
from .pages.home import HomePage


class AmuletLandingWindow(Ui_AmuletLandingWindow):
    def __init__(self):
        super().__init__()

        self.toolbar.add_static_button("amulet:settings", "settings.svg", "Settings")
        # self.toolbar.setProperty("backgroundColor", "surface")
        self.toolbar.add_dynamic_button("amulet:home", "home.svg", "Home")
        self.home = HomePage(self)
        self.settings = SettingsPage(self)
        self.tool_widget.addWidget(self.home)
        self.tool_widget.addWidget(self.settings)

    @Slot(str)
    def _tool_change(self, uid: str):
        pass
