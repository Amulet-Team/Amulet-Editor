from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.project.pages._project import ProjectPage
from amulet_editor.tools.project.panels._project import ProjectPanel
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


class Project(AmuletTool):
    def __init__(self):
        self._page = AmuletView()
        self._primary_panel = AmuletView()
        self._secondary_panel = AmuletView()

        self.view_manager = ProjectManager(self)

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
        return "Project"

    @property
    def icon_name(self) -> str:
        return "folders.svg"


class ProjectManager(QObject):
    def __init__(self, plugin: Project):
        super().__init__()

        self.plugin = plugin

        self.project_page = ProjectPage()

        self.project_panel = ProjectPanel()

        self.set_project_page()
        self.set_project_panel()

    def set_project_page(self):
        page = self.project_page

        self.plugin.set_page(page)

    def set_project_panel(self):
        panel = self.project_panel

        panel.file_selected.connect(self.project_page.show_file)

        self.plugin.set_primary_panel(panel)
