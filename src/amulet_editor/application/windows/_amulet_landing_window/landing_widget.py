from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from amulet_editor import __version__
from amulet_editor.data import build
from amulet_editor.tools.startup._widgets import QIconCard


class AmuletLandingWidget(QWidget):
    """
    A minimal landing page widget.
    No functionality should be implemented here.
    """
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)

        # Amulet Logo
        lbl_app_icon = QLabel()
        lbl_app_icon.setFixedHeight(128)
        lbl_app_icon.setAlignment(Qt.AlignCenter)
        amulet_logo = QPixmap(QImage(build.get_resource("images/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)
        lbl_app_icon.setPixmap(amulet_logo)
        layout.addWidget(lbl_app_icon)

        # Title
        lbl_app_name = QLabel("Amulet Editor")
        lbl_app_name.setAlignment(Qt.AlignCenter)
        lbl_app_name.setProperty("heading", "h1")
        lbl_app_name.setProperty("subfamily", "semi_light")
        layout.addWidget(lbl_app_name)

        # Version number
        lbl_app_version = QLabel(f"Version {__version__}")
        lbl_app_version.setAlignment(Qt.AlignCenter)
        lbl_app_version.setProperty("color", "secondary")
        lbl_app_version.setProperty("heading", "h5")
        lbl_app_version.setProperty("subfamily", "semi_light")
        layout.addWidget(lbl_app_version)

        layout.addSpacing(20)

        # Open World button
        self.crd_open_level = QIconCard(
            build.get_resource(f"icons/tabler/file-symlink.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_open_level.setMinimumWidth(200)
        layout.addWidget(self.crd_open_level, alignment=Qt.AlignCenter)

        # Open Project Button
        self.crd_open_project = QIconCard(
            build.get_resource(f"icons/tabler/file-symlink.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_open_project.setMinimumWidth(200)
        layout.addWidget(self.crd_open_project, alignment=Qt.AlignCenter)

        # New Project button
        self.crd_new_project = QIconCard(
            build.get_resource(f"icons/tabler/file-plus.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_new_project.setMinimumWidth(200)
        layout.addWidget(self.crd_new_project, alignment=Qt.AlignCenter)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.crd_open_level.setText(QCoreApplication.translate("StartupPage", "Open World", None), "h5")
        self.crd_new_project.setText(QCoreApplication.translate("StartupPage", "New Project", None), "h5")
        self.crd_open_project.setText(QCoreApplication.translate("StartupPage", "Open Project", None), "h5")
        # fmt: on
