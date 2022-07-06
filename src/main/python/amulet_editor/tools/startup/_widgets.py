import pathlib
from typing import Optional

from amulet_editor.application import appearance
from amulet_editor.application.appearance import Color, Theme
from amulet_editor.data import build
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.widgets._icon import QSvgIcon
from amulet_editor.models.widgets._label import QElidedLabel
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
    QToolButton,
    QWidget,
)


class QIconButton(QToolButton):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._icon_name = "question-mark"

        appearance.changed.connect(self.retheme)

    def setIcon(self, icon_name: Optional[str] = None) -> None:
        self._icon_name = icon_name

        self.repaint(appearance.theme().on_surface)

    def repaint(self, color: Color) -> None:
        super().setIcon(
            QSvgIcon(
                build.get_resource(f"icons/{self._icon_name}"),
                self.iconSize(),
                color.get_qcolor(),
            )
        )
        self.setStyleSheet(f"color: {color.get_hex()}")

    def retheme(self, theme: Theme) -> None:
        self.repaint(theme.on_surface)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.repaint(appearance.theme().on_primary)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self.isCheckable() and not self.isChecked():
            self.repaint(appearance.theme().on_surface)
        return super().leaveEvent(event)

    def setChecked(self, arg__1: bool) -> None:
        if not arg__1:
            self.repaint(appearance.theme().on_surface)
        return super().setChecked(arg__1)


class QIconCard(QPushButton):
    def __init__(
        self,
        icon: str,
        icon_size: QSize,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)

        self.icon_path = icon
        self.icon_size = icon_size

        self.lbl_icon = QLabel()
        self.lbl_description = QElidedLabel()

        self.lbl_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_icon.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.lbl_description.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QHBoxLayout()
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_description)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.setLayout(layout)
        self.setMinimumHeight(self.icon_size.height() + 10)

        self.repaint(appearance.theme().on_surface)

        appearance.changed.connect(self.retheme)

    def setText(self, text: str, heading: Optional[str]):
        if heading is not None:
            self.lbl_description.setProperty("heading", heading)

        self.lbl_description.setProperty("subfamily", "semi_light")
        self.lbl_description.setText(text)

    def setIcon(self, icon_path: str) -> None:
        if self.icon_path is None:
            layout: QHBoxLayout = self.layout()
            layout.insertWidget(0, self.lbl_icon)
        self.icon_path = icon_path
        self.repaint(appearance.theme().on_surface)

    def repaint(self, color: Color) -> None:
        if self.icon_path is not None:
            self.lbl_icon.setPixmap(
                QSvgIcon(self.icon_path, self.icon_size, color.get_qcolor()).pixmap(
                    self.icon_size
                )
            )
        self.setStyleSheet(f"color: {color.get_hex()}")

    def retheme(self, theme: Theme) -> None:
        self.repaint(theme.on_surface)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.repaint(appearance.theme().on_primary)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.repaint(appearance.theme().on_surface)
        return super().leaveEvent(event)


class QLevelSelectionCard(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.setupUi()

    def setLayout(self, arg__1: QLayout) -> None:
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
            lbl_pixmap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

            lbl_level_name = QElidedLabel(level_name, widget)
            lbl_level_name.setAttribute(Qt.WA_TransparentForMouseEvents)

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

    def setupUi(self) -> None:
        self.swgt_container = QStackedWidget(self)
        self.swgt_container.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.wgt_info = QWidget(self.swgt_container)
        self.wgt_info.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.lbl_info = QLabel(self.wgt_info)
        self.lbl_info.setProperty("color", "on_surface")
        self.lbl_info.setProperty("heading", "h5")
        self.lbl_info.setProperty("subfamily", "semi_light")

        self.lyt_info = QHBoxLayout(self.wgt_info)
        self.lyt_info.addWidget(self.lbl_info)
        self.lyt_info.setAlignment(self.lbl_info, Qt.AlignCenter)
        self.lyt_info.setContentsMargins(0, 0, 0, 0)

        self.wgt_info.setLayout(self.lyt_info)

        self.swgt_container.addWidget(self.wgt_info)

        layout = QHBoxLayout(self)
        layout.addWidget(self.swgt_container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.retranslateUi()

    def retranslateUi(self) -> None:
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_info.setText(QCoreApplication.translate("QLevelSelectionCard", "Click to Select World", None))
        # fmt: on
