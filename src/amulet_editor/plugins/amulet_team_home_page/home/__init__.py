from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from .home import HomePage
from .open_world import OpenWorldPage

from amulet_team_main_window.application.windows.main_window import View
from amulet_team_locale import set_locale


class HomeView(QWidget, View):
    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
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

        @Slot(int)
        def _locale_change(index: int):
            set_locale(page.cbo_language.currentData())

        page.cbo_language.currentIndexChanged.connect(_locale_change)
        self.setCentralWidget(page)

    def _set_open_world_page(self):
        page = OpenWorldPage()
        page.btn_back.clicked.connect(self._set_landing_page)
        self.setCentralWidget(page)
