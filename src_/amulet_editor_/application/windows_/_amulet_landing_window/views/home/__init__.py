from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from amulet_editor.application.windows._amulet_landing_window._view import View
from .home import HomePage
from .open_world import OpenWorldPage


class HomeView(QWidget, View):
    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowFlags = Qt.WindowFlags()
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout(self)
        self._set_landing_page()

    def activate_view(self):
        self._set_landing_page()

    def setCentralWidget(self, widget: QWidget):
        for _ in range(self._layout.count()):
            old_widget = self._layout.takeAt(0)
            if old_widget is not None:
                old_widget.widget().deleteLater()
        self._layout.addWidget(widget)

    def _set_landing_page(self):
        page = HomePage(self)
        # Connect signals
        page.btn_open_world.clicked.connect(self._set_open_world_page)
        # page.crd_new_project.clicked.connect(
        #     partial(self.set_menu_page, NewProjectMenu)
        # )
        self.setCentralWidget(page)

    def _set_open_world_page(self):
        page = OpenWorldPage()
        page.btn_back.clicked.connect(self._set_landing_page)
        self.setCentralWidget(page)
