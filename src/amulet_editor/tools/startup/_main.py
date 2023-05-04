from typing import Optional
from functools import partial

from amulet_editor.data import packages, project
from amulet_editor.models.package import AmuletTool, AmuletView
from amulet_editor.models.widgets import QMenuWidget
from amulet_editor.tools.project import Project
from amulet_editor.tools.startup._models import Menu, Navigate
from amulet_editor.tools.startup.pages._new_project import NewProjectMenu
from amulet_editor.tools.startup.pages._open_world import OpenWorldMenu
from amulet_editor.tools.startup.pages._startup import StartupPage
from amulet_editor.tools.startup.panels._startup import StartupPanel
from PySide6.QtCore import QCoreApplication, QObject
from PySide6.QtWidgets import QWidget


class Startup(AmuletTool):
    def __init__(self):
        self._page = AmuletView()
        self._primary_panel = AmuletView()
        self._secondary_panel = AmuletView()

        self.view_manager = StartupManager(self)

    def set_page(self, widget: QWidget):
        self._page.setWidget(widget)

    def set_primary_panel(self, widget: QWidget):
        self._primary_panel.setWidget(widget)

    def set_secondary_panel(self, widget: Optional[QWidget]):
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
    def __init__(self, plugin: Startup):
        super().__init__()

        self.menu_list: list[Menu] = []
        self.plugin = plugin

        self.startup_page = StartupPage()
        self.startup_panel = StartupPanel()
        self.menu_page = QMenuWidget()

        # Connect signals
        self.startup_page.crd_open_level.clicked.connect(
            partial(self.set_menu_page, OpenWorldMenu)
        )
        self.startup_page.crd_new_project.clicked.connect(
            partial(self.set_menu_page, NewProjectMenu)
        )

        self.menu_page.clicked_cancel.connect(partial(self.set_startup_page))
        self.menu_page.clicked_back.connect(partial(self.menu_back))
        self.menu_page.clicked_next.connect(partial(self.menu_next))

        self.set_startup_page()

    def set_startup_page(self):
        self.close_menu()

        # Set plugin view
        self.plugin.set_page(self.startup_page)
        self.plugin.set_primary_panel(self.startup_panel)
        self.plugin.set_secondary_panel(None)

    def set_menu_page(self, menu_class):
        # Create menu
        menu: Menu = menu_class(self.plugin.set_secondary_panel)
        menu.enable_next.connect(self.menu_page.btn_next.setEnabled)

        self.menu_list.append(menu)
        self.set_menu(menu)

        # Set plugin view
        self.plugin.set_page(self.menu_page)

    def set_menu(self, menu: Menu, new: bool = True):
        # Update menu page
        menu_page = self.menu_page
        menu_page.btn_back.setVisible(menu is not self.menu_list[0])
        menu_page.btn_next.setEnabled(False)
        menu_page.setMenuTitle(menu.title)
        menu_page.setWidget(menu.widget())

        if menu.next_menu() is None:
            menu_page.btn_next.setText(
                QCoreApplication.translate("QMenuWidget", "Finish", None)
            )
        else:
            menu_page.btn_next.setText(
                QCoreApplication.translate("QMenuWidget", "Next", None)
            )

        # Set plugin view
        menu.navigated(Navigate.HERE)
        self.plugin.set_secondary_panel(None)

    def close_menu(self):
        for menu in self.menu_list:
            self.menu_page.removeWidget(menu.widget())
            menu.widget().deleteLater()

        self.menu_list = []

    def menu_back(self):
        current_menu = self.menu_list[-1]
        current_menu.navigated(Navigate.BACK)

        self.menu_list.remove(current_menu)
        self.set_menu(self.menu_list[-1], False)

    def menu_next(self):
        current_menu = self.menu_list[-1]
        current_menu.navigated(Navigate.NEXT)

        if current_menu.next_menu() is not None:
            menu: Menu = current_menu.next_menu()
            menu.enable_next.connect(self.menu_page.btn_next.setEnabled)

            self.menu_list.append(menu)
            self.set_menu(self.menu_list[-1])

    def set_new_project_page(self):
        page = self.new_project_page

        def enable_next(project_name: str):
            project_name = project_name.strip()
            page.btn_next.setEnabled(len(project_name) > 0)

        # Connect signals
        page.lne_project_name.textChanged.connect(enable_next)
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_next.clicked.connect(partial(self.set_import_level_page))

        # Set plugin view
        self.plugin.set_secondary_panel(None)

    def set_import_level_page(self):
        page = self.import_level_page

        # Connect signals
        page.btn_cancel.clicked.connect(partial(self.set_startup_page))
        page.btn_back.clicked.connect(partial(self.set_new_project_page))

        # Set plugin view
        self.plugin.set_secondary_panel(None)

    def set_select_packages_page(self):
        page = self.select_packages_page

        def open_project():
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
        self.plugin.set_secondary_panel(None)
