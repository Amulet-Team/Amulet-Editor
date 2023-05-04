import pathlib
from typing import Optional

from amulet_editor.data import build
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.widgets import AStylableSvgWidget
from amulet_editor.models.widgets import QElidedLabel
from PySide6.QtCore import QCoreApplication, QEvent, QSize, Qt
from PySide6.QtGui import QEnterEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)


class AIconCard(QPushButton):
    def __init__(
        self,
        icon: str,
        icon_size: QSize,
        heading: str = "h5",
        text: str = "",
        *,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.setProperty("hover", "false")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        self.setLayout(layout)

        self._svg_icon = AStylableSvgWidget(build.get_resource(icon))
        self._svg_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._svg_icon.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self._svg_icon.setFixedSize(icon_size)
        layout.addWidget(self._svg_icon)

        self._lbl_description = QElidedLabel()
        self._lbl_description.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._lbl_description.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self._lbl_description.setProperty("subfamily", "semi_light")
        self._lbl_description.setText(text)
        self._lbl_description.setProperty("heading", heading)
        layout.addWidget(self._lbl_description)

        self.setMinimumHeight(icon_size.height() + 10)

    def setText(self, text: str):
        self._lbl_description.setText(text)

    def setHeading(self, heading: str):
        self._lbl_description.setProperty("heading", heading)

    def setIcon(self, icon_path: str):
        self._svg_icon.load(build.get_resource(icon_path))

    def enterEvent(self, event: QEnterEvent):
        self.setProperty("hover", "true")
        self.setStyleSheet("/* /")  # Force a style update.
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        if not self.isChecked():
            self.setProperty("hover", "false")
        self.setStyleSheet("/* /")  # Force a style update.
        super().leaveEvent(event)


class QLevelSelectionCard(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.setupUi()

    def setLayout(self, arg__1: QLayout):
        return None

    def setLevel(self, level_data: Optional[LevelData]):
        if level_data is not None:
            icon_path = (
                level_data.icon_path
                if level_data.icon_path is not None
                else build.get_resource("images/missing_world_icon.png")
            )
            level_icon = QPixmap(QImage(icon_path))
            level_icon = level_icon.scaledToHeight(80)

            level_name = level_data.name.get_html(font_weight=600)
            file_name = pathlib.PurePath(level_data.path).name
            version = f"{level_data.edition} - {level_data.version}"
            last_played = (
                level_data.last_played.astimezone(tz=None)
                .strftime("%B %d, %Y %I:%M %p")
                .replace(" 0", " ")
            )

            widget = QWidget(self.swgt_container)
            grid = QGridLayout(widget)

            lbl_pixmap = QLabel(widget)
            lbl_pixmap.setPixmap(level_icon)
            lbl_pixmap.setProperty("backgroundColor", "background")
            lbl_pixmap.setProperty("border", "surface")
            lbl_pixmap.setProperty("borderRadiusVisible", True)
            lbl_pixmap.setSizePolicy(
                QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
            )

            lbl_level_name = QElidedLabel(level_name, widget)
            lbl_level_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            lbl_file_name = QElidedLabel(file_name, widget)

            lbl_version = QElidedLabel(version, widget)

            lbl_last_played = QElidedLabel(last_played, widget)

            grid.addWidget(lbl_pixmap, 0, 0, 4, 1)
            grid.addWidget(lbl_level_name, 0, 1, 1, 1)
            grid.addWidget(lbl_file_name, 1, 1, 1, 1)
            grid.addWidget(lbl_version, 2, 1, 1, 1)
            grid.addWidget(lbl_last_played, 3, 1, 1, 1)

            widget.setLayout(grid)

            if self.swgt_container.widget(1) is not None:
                self.swgt_container.removeWidget(self.swgt_container.widget(1))

            self.swgt_container.addWidget(widget)
            self.swgt_container.setCurrentIndex(1)
        else:
            self.swgt_container.setCurrentIndex(0)

    def layout(self) -> QHBoxLayout:
        return super().layout()

    def setupUi(self):
        self.swgt_container = QStackedWidget(self)
        self.swgt_container.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.wgt_info = QWidget(self.swgt_container)
        self.wgt_info.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.lbl_info = QLabel(self.wgt_info)
        self.lbl_info.setProperty("color", "on_surface")
        self.lbl_info.setProperty("heading", "h5")
        self.lbl_info.setProperty("subfamily", "semi_light")

        self.lyt_info = QHBoxLayout(self.wgt_info)
        self.lyt_info.addWidget(self.lbl_info)
        self.lyt_info.setAlignment(self.lbl_info, Qt.AlignmentFlag.AlignCenter)
        self.lyt_info.setContentsMargins(0, 0, 0, 0)

        self.wgt_info.setLayout(self.lyt_info)

        self.swgt_container.addWidget(self.wgt_info)

        layout = QHBoxLayout(self)
        layout.addWidget(self.swgt_container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_info.setText(QCoreApplication.translate("QLevelSelectionCard", "Click to Select World", None))
        # fmt: on
