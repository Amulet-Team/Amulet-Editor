from amulet_editor.data import build
from amulet_editor.data.build import PUBLIC_DATA
from amulet_editor.tools.startup._widgets import QIconCard
from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StartupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setupUi()

        # self.frm_nav_header = QFrame(self)
        # self.frm_nav_header.setFixedHeight(25)
        # self.frm_nav_header.setFrameShape(QFrame.NoFrame)
        # self.frm_nav_header.setFrameShadow(QFrame.Raised)
        # self.frm_nav_header.setProperty("backgroundColor", "primary")
        # self.frm_nav_header.setProperty("borderBottom", "surface")
        # self.frm_nav_header.setProperty("color", "on_surface")

    def setupUi(self):
        amulet_logo = QPixmap(QImage(build.get_resource("images/amulet_logo.png")))
        amulet_logo = amulet_logo.scaledToHeight(128)

        self.lbl_app_icon = QLabel()
        self.lbl_app_icon.setFixedHeight(128)
        self.lbl_app_icon.setAlignment(Qt.AlignCenter)
        self.lbl_app_icon.setPixmap(amulet_logo)

        self.lbl_app_name = QLabel("Amulet Editor")
        self.lbl_app_name.setAlignment(Qt.AlignCenter)
        self.lbl_app_name.setProperty("heading", "h1")
        self.lbl_app_name.setProperty("subfamily", "semi_light")

        self.lbl_app_version = QLabel(f"Version {PUBLIC_DATA['version']}")
        self.lbl_app_version.setAlignment(Qt.AlignCenter)
        self.lbl_app_version.setProperty("color", "secondary")
        self.lbl_app_version.setProperty("heading", "h5")
        self.lbl_app_version.setProperty("subfamily", "semi_light")

        self.crd_open_level = QIconCard(
            build.get_resource(f"icons/file-symlink.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_open_level.setMinimumWidth(200)

        self.crd_open_project = QIconCard(
            build.get_resource(f"icons/file-symlink.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_open_project.setMinimumWidth(200)

        self.crd_new_project = QIconCard(
            build.get_resource(f"icons/file-plus.svg"),
            QSize(25, 25),
            self,
        )
        self.crd_new_project.setMinimumWidth(200)

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_app_icon)
        layout.addWidget(self.lbl_app_name)
        layout.addWidget(self.lbl_app_version)
        layout.addSpacing(20)
        layout.addWidget(self.crd_open_level)
        layout.addWidget(self.crd_open_project)
        layout.addWidget(self.crd_new_project)

        layout.setAlignment(Qt.AlignCenter)
        layout.setAlignment(self.crd_open_level, Qt.AlignCenter)
        layout.setAlignment(self.crd_open_project, Qt.AlignCenter)
        layout.setAlignment(self.crd_new_project, Qt.AlignCenter)
        layout.setSpacing(5)

        self.setLayout(layout)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.crd_open_level.setText(QCoreApplication.translate("StartupPage", "Open World", None), "h5")
        self.crd_new_project.setText(QCoreApplication.translate("StartupPage", "New Project", None), "h5")
        self.crd_open_project.setText(QCoreApplication.translate("StartupPage", "Open Project", None), "h5")
        # fmt: on
