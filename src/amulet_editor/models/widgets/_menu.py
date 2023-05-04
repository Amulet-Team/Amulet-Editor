from typing import Optional

from PySide6.QtCore import QCoreApplication, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class QMenuWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setupUi()

    @property
    def clicked_cancel(self) -> Signal:
        return self.btn_cancel.clicked

    @property
    def clicked_back(self) -> Signal:
        return self.btn_back.clicked

    @property
    def clicked_next(self) -> Signal:
        return self.btn_next.clicked

    def setMenuTitle(self, text: str):
        self._lbl_menu_title.setText(text)

    def menuTitle(self) -> str:
        return self._lbl_menu_title.text()

    def setWidget(self, widget: QWidget):
        if widget not in self._swgt_menu.children():
            self._swgt_menu.addWidget(widget)
        self._swgt_menu.setCurrentWidget(widget)

    def removeWidget(self, widget: QWidget):
        self._swgt_menu.removeWidget(widget)

    def setupUi(self):
        # Create 'Menu' frame
        frm_menu = QFrame(self)
        frm_menu.setFrameShape(QFrame.Shape.NoFrame)
        frm_menu.setFrameShadow(QFrame.Shadow.Raised)
        frm_menu.setMaximumWidth(750)

        # Create 'Header' frame
        frm_menu_header = QFrame(frm_menu)

        lbl_menu_header = QLabel(frm_menu_header)
        lbl_menu_header.setProperty("heading", "h3")
        lbl_menu_header.setProperty("subfamily", "semi_light")

        lyt_menu_header = QHBoxLayout(frm_menu_header)
        lyt_menu_header.addWidget(lbl_menu_header)
        lyt_menu_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lyt_menu_header.setContentsMargins(0, 0, 0, 5)
        lyt_menu_header.setSpacing(5)

        frm_menu_header.setFrameShape(QFrame.Shape.NoFrame)
        frm_menu_header.setFrameShadow(QFrame.Shadow.Raised)
        frm_menu_header.setLayout(lyt_menu_header)

        # Create swappable 'Menu Container' widget
        swgt_menu = QStackedWidget()
        swgt_menu.setProperty("backgroundColor", "background")

        # Create 'Menu Container' widget
        scr_menu = QScrollArea(frm_menu)
        scr_menu.setFrameShape(QFrame.Shape.NoFrame)
        scr_menu.setFrameShadow(QFrame.Shadow.Raised)
        scr_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scr_menu.setProperty("borderBottom", "surface")
        scr_menu.setProperty("borderTop", "surface")
        scr_menu.setProperty("backgroundColor", "background")
        scr_menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scr_menu.setWidgetResizable(True)
        scr_menu.setWidget(swgt_menu)

        # Create 'Page Options' frame
        frm_menu_options = QFrame(frm_menu)

        # Configure 'Menu Options' widgets
        btn_cancel = QPushButton(frm_menu_options)
        btn_cancel.setFixedHeight(30)

        btn_back = QPushButton(frm_menu_options)
        btn_back.setFixedHeight(30)

        btn_next = QPushButton(frm_menu_options)
        btn_next.setFixedHeight(30)
        btn_next.setProperty("backgroundColor", "secondary")

        # Create 'Menu Options' layout
        lyt_menu_options = QHBoxLayout(frm_menu)
        lyt_menu_options.addWidget(btn_cancel)
        lyt_menu_options.addStretch()
        lyt_menu_options.addWidget(btn_back)
        lyt_menu_options.addWidget(btn_next)
        lyt_menu_options.setContentsMargins(0, 10, 0, 5)
        lyt_menu_options.setSpacing(5)

        # Configure 'Menu Options' frame
        frm_menu_options.setFrameShape(QFrame.Shape.NoFrame)
        frm_menu_options.setFrameShadow(QFrame.Shadow.Raised)
        frm_menu_options.setLayout(lyt_menu_options)

        # Create 'Menu' layout
        lyt_menu = QVBoxLayout(frm_menu)
        lyt_menu.addWidget(frm_menu_header)
        lyt_menu.addWidget(scr_menu)
        lyt_menu.addWidget(frm_menu_options)
        lyt_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lyt_menu.setSpacing(5)

        layout = QVBoxLayout(self)
        layout.addWidget(frm_menu)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)

        self._lbl_menu_title = lbl_menu_header
        self._swgt_menu = swgt_menu
        self.btn_cancel = btn_cancel
        self.btn_back = btn_back
        self.btn_next = btn_next

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.btn_cancel.setText(QCoreApplication.translate("QMenuWidget", "Cancel", None))
        self.btn_back.setText(QCoreApplication.translate("QMenuWidget", "Back", None))
        self.btn_next.setText(QCoreApplication.translate("QMenuWidget", "Next", None))
        # fmt: on
