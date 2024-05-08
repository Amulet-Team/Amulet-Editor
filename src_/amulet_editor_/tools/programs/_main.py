from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.programs.pages._programs import ProgramsPage
from amulet_editor.tools.programs.panels._programs import ProgramsPanel
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


class Programs(AmuletTool):
    def __init__(self):
        self._page = AmuletView()
        self._primary_panel = AmuletView()
        self._secondary_panel = AmuletView()

        self.view_manager = ProgramsManager(self)

    def set_page(self, widget: QWidget):
        self._page.setWidget(widget)

    def set_primary_panel(self, widget: QWidget):
        self._primary_panel.setWidget(widget)

    def set_secondary_panel(self, widget: QWidget):
        self._secondary_panel.setWidget(widget)

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
        return "Programs"

    @property
    def icon_name(self) -> str:
        return "app-window.svg"


class ProgramsManager(QObject):
    def __init__(self, plugin: Programs):
        super().__init__()

        self.plugin = plugin

        self.programs_page = ProgramsPage()

        self.programs_panel = ProgramsPanel()

        self.set_programs_page()
        self.set_programs_panel()

    def set_programs_page(self):
        page = self.programs_page

        self.plugin.set_page(page)

    def set_programs_panel(self):
        panel = self.programs_panel

        self.plugin.set_primary_panel(panel)
