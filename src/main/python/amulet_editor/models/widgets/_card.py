from typing import Optional

from amulet_editor.data import build
from amulet_editor.application import appearance
from amulet_editor.application.appearance import Color, Theme
from amulet_editor.models.widgets._icon import QSvgIcon
from amulet_editor.models.widgets._label import QElidedLabel
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QEnterEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class QPixCard(QPushButton):
    def __init__(self, pixmap: QPixmap, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)

        self._pixmap = QLabel()
        self._pixmap.setPixmap(pixmap)
        self._pixmap.setProperty("backgroundColor", "background")
        self._pixmap.setProperty("border", "surface")
        self._pixmap.setProperty("borderRadiusVisible", True)
        self._pixmap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setAttribute(Qt.WA_TransparentForMouseEvents)
        frame.setLayout(layout)

        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.addWidget(self._pixmap)
        layout.addWidget(frame)
        self.setLayout(layout)

    def addLabel(self, text: str):
        label = QElidedLabel(text, self)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.layout().itemAt(1).widget().layout().addWidget(label)

    def layout(self) -> QHBoxLayout:
        return super().layout()


class QLinkCard(QPushButton):
    def __init__(
        self,
        text: str,
        icon: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)

        self.icon_size = QSize(15, 15)
        self.icon_path = icon
        self.icon_link = build.get_resource(f"icons/external-link.svg")

        self.lbl_link_icon = QLabel()
        self.lbl_description = QElidedLabel()
        self.lbl_ext_icon = QLabel()

        self.lbl_link_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_link_icon.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.lbl_description.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.lbl_ext_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_ext_icon.setPixmap(
            QSvgIcon(
                self.icon_link,
                self.icon_size,
                appearance.theme().on_primary.get_qcolor(),
            ).pixmap(self.icon_size)
        )
        self.lbl_ext_icon.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        layout = QHBoxLayout()
        if self.icon_path is not None:
            layout.addWidget(self.lbl_link_icon)
        layout.addWidget(self.lbl_description)
        layout.addWidget(self.lbl_ext_icon)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.setLayout(layout)
        self.setMinimumSize(self.minimumSizeHint())

        self.setProperty("auto_hide", True)

        self.lbl_description.setText(text)
        self.lbl_ext_icon.setHidden(True)
        self.repaint(appearance.theme().on_surface)

        appearance.changed.connect(self.retheme)

    def setIcon(self, icon_path: str) -> None:
        if self.icon_path is None:
            layout: QHBoxLayout = self.layout()
            layout.insertWidget(0, self.lbl_link_icon)
        self.icon_path = icon_path
        self.repaint(appearance.theme().on_surface)

    def repaint(self, color: Color) -> None:
        if self.icon_path is not None:
            self.lbl_link_icon.setPixmap(
                QSvgIcon(self.icon_path, self.icon_size, color.get_qcolor()).pixmap(
                    self.icon_size
                )
            )
        self.setStyleSheet(f"color: {color.get_hex()}")

    def retheme(self, theme: Theme) -> None:
        self.repaint(theme.on_surface)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.repaint(appearance.theme().on_primary)
        self.lbl_ext_icon.setHidden(False)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.repaint(appearance.theme().on_surface)
        self.lbl_ext_icon.setHidden(True)
        return super().leaveEvent(event)
