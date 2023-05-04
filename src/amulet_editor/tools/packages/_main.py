from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.packages._pages import PackagesPage
from amulet_editor.tools.packages._panels import PackagesPanel


class Packages(AmuletTool):
    def __init__(self):
        self._page = AmuletView(PackagesPage())
        self._primary_panel = AmuletView(PackagesPanel())
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
        return "Packages"

    @property
    def icon_name(self) -> str:
        return "package.svg"
