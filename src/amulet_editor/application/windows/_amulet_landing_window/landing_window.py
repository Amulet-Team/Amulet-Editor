from PySide6.QtWidgets import QMainWindow
from .pages.home import HomePage
from .pages.open_world import OpenWorldPage


class AmuletLandingWindow(QMainWindow):
    """A minimal landing page."""
    def __init__(self) -> None:
        super().__init__()
        self._set_landing_page()

    def _set_landing_page(self):
        page = HomePage(self)
        # Connect signals
        page.btn_open_world.clicked.connect(
            self._set_open_world_page
        )
        # page.crd_new_project.clicked.connect(
        #     partial(self.set_menu_page, NewProjectMenu)
        # )
        self.setCentralWidget(page)

    def _set_open_world_page(self):
        page = OpenWorldPage()
        page.btn_back.clicked.connect(self._set_landing_page)
        self.setCentralWidget(page)

    # def set_new_project_page(self) -> None:
    #     page = self.new_project_page
    #
    #     def enable_next(project_name: str) -> None:
    #         project_name = project_name.strip()
    #         page.btn_next.setEnabled(len(project_name) > 0)
    #
    #     # Connect signals
    #     page.lne_project_name.textChanged.connect(enable_next)
    #     page.btn_cancel.clicked.connect(partial(self.set_startup_page))
    #     page.btn_next.clicked.connect(partial(self.set_import_level_page))
    #
    # def set_import_level_page(self) -> None:
    #     page = self.import_level_page
    #
    #     # Connect signals
    #     page.btn_cancel.clicked.connect(partial(self.set_startup_page))
    #     page.btn_back.clicked.connect(partial(self.set_new_project_page))
