import webbrowser
from dataclasses import dataclass
from functools import partial

from amulet_editor.data import build
from amulet_editor.models.widgets import ALinkCard
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


@dataclass
class LinkData:
    name: str
    icon: str
    url: str


class StartupPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.wgt_links = QWidget(self)
        self.wgt_links.setProperty("backgroundColor", "background")
        self.wgt_links.setProperty("border", "surface")
        self.wgt_links.setProperty("borderRadiusVisible", True)

        self.lbl_links = QLabel(self.wgt_links)
        self.lbl_links.setProperty("color", "on_primary")

        self.lyt_links = QVBoxLayout(self.wgt_links)
        self.lyt_links.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lyt_links.setSpacing(5)

        self.setLayout(QVBoxLayout(self))
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.wgt_links)

        links: list[LinkData] = [
            LinkData(
                "Website",
                "world.svg",
                "https://www.amuletmc.com/",
            ),
            LinkData(
                "GitHub",
                "brand-github.svg",
                "https://github.com/Amulet-Team/Amulet-Map-Editor",
            ),
            LinkData(
                "Discord",
                "brand-discord.svg",
                "https://www.amuletmc.com/discord",
            ),
            LinkData(
                "Feedback",
                "flag.svg",
                "https://github.com/Amulet-Team/Amulet-Map-Editor/issues/new/choose",
            ),
        ]

        self.wgt_links.layout().addWidget(self.lbl_links)
        for link in links:
            link_card = ALinkCard(
                link.name,
                build.get_resource(f"icons/tabler/{link.icon}"),
                self.wgt_links,
            )
            link_card.clicked.connect(partial(webbrowser.open, link.url))
            self.wgt_links.layout().addWidget(link_card)

        self.wgt_links.setMaximumHeight(self.wgt_links.minimumSizeHint().height())

        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_links.setText(QCoreApplication.translate("StartupPanel", "External Links", None))
        # fmt: on
