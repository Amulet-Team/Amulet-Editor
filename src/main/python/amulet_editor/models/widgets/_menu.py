from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class QMenuWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self.setupUi()

    def setMenuName(self, text: str) -> None:
        self._lbl_menu_name.setText(text)

    def menuName(self) -> str:
        self._lbl_menu_name.text()

    def setWidget(self, widget: QWidget) -> None:
        self._scr_menu.setWidget(widget)

    def widget(self) -> Optional[QWidget]:
        self._scr_menu.widget()

    def setupUi(self):
        # Create 'Header' frame
        frm_menu_header = QFrame(self)

        lbl_menu_header = QLabel(frm_menu_header)
        lbl_menu_header.setProperty("heading", "h3")
        lbl_menu_header.setProperty("subfamily", "semi_light")

        lyt_menu_header = QHBoxLayout(frm_menu_header)
        lyt_menu_header.addWidget(lbl_menu_header)
        lyt_menu_header.setAlignment(Qt.AlignLeft)
        lyt_menu_header.setContentsMargins(0, 0, 0, 10)
        lyt_menu_header.setSpacing(5)

        frm_menu_header.setFrameShape(QFrame.NoFrame)
        frm_menu_header.setFrameShadow(QFrame.Raised)
        frm_menu_header.setLayout(lyt_menu_header)
        frm_menu_header.setProperty("borderBottom", "surface")
        frm_menu_header.setProperty("borderTop", "background")

        # Create 'Menu Container' widget
        scr_menu = QScrollArea()
        scr_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scr_menu.setProperty("style", "background")
        scr_menu.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scr_menu.setWidgetResizable(True)

        # Create 'Page Options' frame
        frm_menu_options = QFrame(self)

        # Configure 'Menu Options' widgets
        btn_cancel = QPushButton(frm_menu_options)
        btn_cancel.setFixedHeight(30)

        btn_back = QPushButton(frm_menu_options)
        btn_back.setFixedHeight(30)

        btn_next = QPushButton(frm_menu_options)
        btn_next.setFixedHeight(30)
        btn_next.setProperty("backgroundColor", "secondary")

        # Create 'Menu Options' layout
        lyt_menu_options = QHBoxLayout(self)
        lyt_menu_options.addWidget(btn_cancel)
        lyt_menu_options.addStretch()
        lyt_menu_options.addWidget(btn_back)
        lyt_menu_options.addWidget(btn_next)
        lyt_menu_options.setContentsMargins(0, 10, 0, 5)
        lyt_menu_options.setSpacing(5)

        # Configure 'Menu Options' frame
        frm_menu_options.setFrameShape(QFrame.NoFrame)
        frm_menu_options.setFrameShadow(QFrame.Raised)
        frm_menu_options.setLayout(lyt_menu_options)
        frm_menu_options.setProperty("borderTop", "surface")

        # Create 'Menu' layout
        layout = QVBoxLayout(self)
        layout.addWidget(frm_menu_header)
        layout.addWidget(scr_menu)
        layout.addWidget(frm_menu_options)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.setSpacing(5)

        self.setLayout(layout)
        self.setMaximumWidth(750)

        self._lbl_menu_name = lbl_menu_header
        self._scr_menu = scr_menu
        self._btn_cancel = btn_cancel
        self._btn_back = btn_back
        self._btn_next = btn_next
