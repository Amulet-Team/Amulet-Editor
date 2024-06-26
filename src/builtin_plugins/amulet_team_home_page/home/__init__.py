from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from .home import HomePage
from .open_world import OpenWorldPage

from amulet_team_main_window import TabWidget
from amulet_team_locale import set_locale


class HomeWidget(TabWidget):
    name = "Home"

    def __init__(
        self, parent: Optional[QWidget] = None, f: Qt.WindowType = Qt.WindowType.Widget
    ):
        super().__init__(parent, f)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._set_landing_page()

    def setCentralWidget(self, widget: QWidget) -> None:
        for _ in range(self._layout.count()):
            old_layout_item = self._layout.takeAt(0)
            if old_layout_item is not None:
                old_widget = old_layout_item.widget()
                if old_widget is not None:
                    old_widget.deleteLater()
        self._layout.addWidget(widget)

    def _set_landing_page(self) -> None:
        page = HomePage(self)
        # Connect signals
        page.btn_open_world.clicked.connect(self._set_open_world_page)
        # page.crd_new_project.clicked.connect(
        #     partial(self.set_menu_page, NewProjectMenu)
        # )

        @Slot(int)
        def _locale_change(index: int) -> None:
            set_locale(page.cbo_language.currentData())

        page.cbo_language.currentIndexChanged.connect(_locale_change)
        self.setCentralWidget(page)

    def _set_open_world_page(self) -> None:
        page = OpenWorldPage()
        page.btn_back.clicked.connect(self._set_landing_page)
        self.setCentralWidget(page)
