from typing import Optional

from amulet_editor.data import build
from PySide6.QtCore import QEvent, Qt
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

from ._icon import AStylableSvgWidget
from ._label import QElidedLabel


class QPixCard(QPushButton):
    def __init__(self, pixmap: QPixmap, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)

        self._pixmap = QLabel()
        self._pixmap.setPixmap(pixmap)
        self._pixmap.setProperty("backgroundColor", "background")
        self._pixmap.setProperty("border", "surface")
        self._pixmap.setProperty("borderRadiusVisible", True)
        self._pixmap.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        frame.setLayout(layout)

        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(self._pixmap)
        layout.addWidget(frame)
        self.setLayout(layout)

    def addLabel(self, text: str):
        label = QElidedLabel(text, self)
        self.layout().itemAt(1).widget().layout().addWidget(label)

    def layout(self) -> QHBoxLayout:
        return super().layout()


class ALinkCard(QPushButton):
    svg_link_icon: Optional[AStylableSvgWidget]

    def __init__(
        self,
        text: str,
        icon: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.setProperty("hover", "false")  # X:hover > Y style is broken.

        layout = QHBoxLayout()

        if icon:
            self.svg_link_icon = AStylableSvgWidget(icon)
            self.svg_link_icon.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
            self.svg_link_icon.setFixedSize(15, 15)
            layout.addWidget(self.svg_link_icon)
        else:
            self.svg_link_icon = None

        self.lbl_description = QElidedLabel(text)
        self.lbl_description.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.lbl_description.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        layout.addWidget(self.lbl_description)

        self.svg_ext_icon = AStylableSvgWidget(
            build.get_resource(f"icons/tabler/external-link.svg")
        )
        self.svg_ext_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.svg_ext_icon.setFixedSize(15, 15)
        self.svg_ext_icon.setHidden(True)
        layout.addWidget(self.svg_ext_icon)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.setLayout(layout)
        self.setMinimumSize(self.minimumSizeHint())

    def enterEvent(self, event: QEnterEvent):
        self.svg_ext_icon.setHidden(False)
        self.setProperty("hover", "true")
        self.setStyleSheet("/* /")  # Force a style update.
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.svg_ext_icon.setHidden(True)
        self.setProperty("hover", "false")
        self.setStyleSheet("/* /")  # Force a style update.
        super().leaveEvent(event)
