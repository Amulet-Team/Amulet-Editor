from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class HomePageGui(QWidget):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)

        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(5)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._left_spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._layout.addItem(self._left_spacer)

        self._central_layout = QVBoxLayout()
        self._central_layout.setContentsMargins(50, 50, 50, 50)

        self._top_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self._central_layout.addItem(self._top_spacer)

        self._lbl_app_icon = QLabel(self)
        self._lbl_app_icon.setMinimumSize(QSize(0, 128))
        self._lbl_app_icon.setMaximumSize(QSize(16777215, 128))
        self._lbl_app_icon.setText("")
        self._lbl_app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(self._lbl_app_icon)

        self._lbl_app_name = QLabel(self)
        self._lbl_app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_app_name.setProperty("subfamily", "semi_light")
        self._lbl_app_name.setProperty("heading", "h1")
        self._central_layout.addWidget(self._lbl_app_name)

        self._lbl_app_version = QLabel(self)
        self._lbl_app_version.setText("")
        self._lbl_app_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_app_version.setProperty("color", "secondary")
        self._lbl_app_version.setProperty("heading", "h5")
        self._lbl_app_version.setProperty("subfamily", "semi_light")
        self._central_layout.addWidget(self._lbl_app_version)

        self._middle_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self._central_layout.addItem(self._middle_spacer)

        self._widget_layout = QVBoxLayout()

        self._open_layout = QHBoxLayout()

        self.horizontalSpacer = QSpacerItem(
            3, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._open_layout.addItem(self.horizontalSpacer)

        self._lbl_open_level = QLabel(self)
        self._open_layout.addWidget(self._lbl_open_level)

        self.btn_open_world = QPushButton(self)
        self._open_layout.addWidget(self.btn_open_world)
        self._widget_layout.addLayout(self._open_layout)

        self._language = QComboBox(self)
        self._widget_layout.addWidget(self._language)

        self._theme_layout = QHBoxLayout()

        self._style = QComboBox(self)
        self._theme_layout.addWidget(self._style)

        self._colour_scheme = QPushButton(self)
        self._colour_scheme.setCheckable(True)
        self._theme_layout.addWidget(self._colour_scheme)
        self._widget_layout.addLayout(self._theme_layout)
        self._central_layout.addLayout(self._widget_layout)

        self._bottom_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self._central_layout.addItem(self._bottom_spacer)
        self._layout.addLayout(self._central_layout)

        self._right_spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._layout.addItem(self._right_spacer)

        # self._quick_access = QWidget(self)
        # self._layout.addWidget(self._quick_access)
        # self._layout.setStretch(0, 1)
        # self._layout.setStretch(2, 1)

        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate("plugin.amulet.editor.HomePage", "Home", None)
        )
        self._lbl_app_name.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.HomePage", "amulet_editor", None
            )
        )
        self._lbl_open_level.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.HomePage", "lbl_open_level", None
            )
        )
        self.btn_open_world.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.HomePage", "btn_open_level", None
            )
        )
