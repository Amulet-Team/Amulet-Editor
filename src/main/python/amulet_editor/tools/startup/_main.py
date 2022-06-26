from functools import partial
from typing import Callable, Optional

from amulet_editor.data import packages, project
from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.tools.project import Project
from amulet_editor.tools.startup.pages._import_level import ImportLevelPage
from amulet_editor.tools.startup.pages._new_project import NewProjectPage
from amulet_editor.tools.startup.pages._open_world import OpenWorldPage
from amulet_editor.tools.startup.pages._select_packages import SelectPackagesPage
from amulet_editor.tools.startup.pages._startup import StartupPage
from amulet_editor.tools.startup.panels._startup import StartupPanel
from amulet_editor.tools.startup.panels._world_selection import WorldSelectionPanel
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


class Startup(AmuletTool):
    def __init__(self) -> None:

        self._page = AmuletView()
        self._primary_panel = AmuletView()
        self._secondary_panel = AmuletView()

        self.view_manager = StartupManager(self)

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
        return "Startup"

    @property
    def icon_name(self) -> str:
        return "hexagons.svg"


class StartupManager(QObject):
    def __init__(self, plugin: Startup) -> None:
        super().__init__()

        self.project_root: str = None

        self.plugin = plugin

        self.startup_page = StartupPage()
        self.open_world_page: Optional[OpenWorldPage] = None
        self.new_project_page: Optional[NewProjectPage] = None
        self.import_level_page: Optional[ImportLevelPage] = None
        self.select_packages_page: Optional[SelectPackagesPage] = None

        self.startup_panel = StartupPanel()
        self.world_selection_panel: Optional[WorldSelectionPanel] = None

        self.set_startup_page()
        self.set_startup_panel()

    def set_startup_page(self) -> None:
        page = self.startup_page

        if self.open_world_page is not None:
            self.open_world_page.deleteLater()
        if self.new_project_page is not None:
            self.new_project_page.deleteLater()
        if self.import_level_page is not None:
            self.import_level_page.deleteLater()
        if self.select_packages_page is not None:
            self.select_packages_page.deleteLater()

        self.open_world_page = OpenWorldPage()
        self.new_project_page = NewProjectPage()
        self.import_level_page = ImportLevelPage()
        self.select_packages_page = SelectPackagesPage()

        if self.world_selection_panel is not None:
            self.world_selection_panel.deleteLater()

        self.world_selection_panel = WorldSelectionPanel()

        # Disconnect signals if connected
        try:
            page.crd_open_level.clicked.disconnect()
        except RuntimeError:
            pass
        try:
            page.crd_new_project.clicked.disconnect()
        except RuntimeError:
            pass

        # Connect signals
        page.crd_open_level.clicked.connect(partial(self.set_open_world_page))
        page.crd_new_project.clicked.connect(partial(self.set_new_project_page))

        # Set plugin view
        self.plugin.set_page(page)
        self.plugin.set_secondary_panel(None)

    def set_open_world_page(self) -> None:
        page = self.open_world_page

        def select_level():
            if not page.crd_select_level.isChecked():
                self.plugin.set_secondary_panel(None)
            elif self.plugin.secondary_panel.widget() is not self.world_selection_panel:
                self.set_world_selection_panel(page.select_level)

        def next():
            self.project_root = page.level_directory
            self.set_select_packages_page()

        # Connect signals
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_next.clicked.connect(partial(next))
        page.crd_select_level.clicked.connect(partial(select_level))

        # Set plugin view
        self.plugin.set_page(page)
        self.plugin.set_secondary_panel(None)

    def set_new_project_page(self) -> None:
        page = self.new_project_page

        def enable_next(project_name: str) -> None:
            project_name = project_name.strip()
            page.btn_next.setEnabled(len(project_name) > 0)

        # Connect signals
        page.lne_project_name.textChanged.connect(enable_next)
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_next.clicked.connect(partial(self.set_import_level_page))

        # Set plugin view
        self.plugin.set_page(page)
        self.plugin.set_secondary_panel(None)

    def set_import_level_page(self) -> None:
        page = self.import_level_page

        # Connect signals
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_back.clicked.connect(partial(self.set_new_project_page))

        # Set plugin view
        self.plugin.set_page(page)
        self.plugin.set_secondary_panel(None)

    def set_select_packages_page(self) -> None:
        page = self.select_packages_page

        def open_project() -> None:
            tools = packages.list_tools()
            for tool in tools:
                packages.disable_tool(tool)

            packages.enable_tool(Project())
            project.set_root(self.project_root)

        # Connect signals
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_back.clicked.connect(partial(self.set_open_world_page))
        page.btn_next.clicked.connect(partial(open_project))

        # Set plugin view
        self.plugin.set_page(page)
        self.plugin.set_secondary_panel(None)

    def set_startup_panel(self) -> None:
        self.plugin.set_primary_panel(self.startup_panel)

    def set_world_selection_panel(self, callback: Callable):

        # Connect signals
        self.world_selection_panel.level_data.connect(callback)

        # Set secondary panel
        self.plugin.set_secondary_panel(self.world_selection_panel)
