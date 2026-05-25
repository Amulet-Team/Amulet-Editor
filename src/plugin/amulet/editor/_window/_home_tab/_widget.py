from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout

from ._home_page import HomePage
from ._open_world_page import OpenWorldPage


class HomeWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._set_landing_page()

    def _set_central_widget(self, widget: QWidget) -> None:
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
        self._set_central_widget(page)

    def _set_open_world_page(self) -> None:
        page = OpenWorldPage()
        page.btn_back.clicked.connect(self._set_landing_page)
        self._set_central_widget(page)
