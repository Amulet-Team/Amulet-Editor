import pathlib
from dataclasses import dataclass
from distutils.version import StrictVersion
from functools import partial
from typing import Optional

import amulet
from amulet_editor.data import build, minecraft
from amulet_editor.models.minecraft import LevelData
from amulet_editor.models.widgets import QPixCard, AIconButton
from PySide6.QtCore import QCoreApplication, QObject, QSize, Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ParsedLevel:
    level_data: LevelData
    icon_path: str = ""
    level_name: str = ""
    file_name: str = ""
    version: str = ""
    last_played: str = ""


class LevelParser(QObject):
    parsed_level = Signal(ParsedLevel)

    @Slot(str)
    def parse_level(self, level_path: str):
        level_data = LevelData(amulet.load_format(level_path))
        parsed_level = ParsedLevel(level_data)

        parsed_level.icon_path = (
            level_data.icon_path
            if level_data.icon_path is not None
            else build.get_resource("images/missing_world_icon.png")
        )
        parsed_level.level_name = level_data.name.get_html(font_weight=600)
        parsed_level.file_name = pathlib.PurePath(level_data.path).name
        parsed_level.version = f"{level_data.edition} - {level_data.version}"
        parsed_level.last_played = (
            level_data.last_played.astimezone(tz=None)
            .strftime("%B %d, %Y %I:%M %p")
            .replace(" 0", " ")
        )

        self.parsed_level.emit(parsed_level)


class WorldSelectionPanel(QWidget):
    level_data = Signal(LevelData)
    parse = Signal(str)

    def __init__(self):
        super().__init__()

        self.setupUi()

        self.cbx_version.addItem("Any")

        self.cbx_edition.addItem("Any")

        self.cbx_sort.addItem("Last Played")
        self.cbx_sort.addItem("Name")

        self._sort_descending = True

        self._parsing_thread = QThread()
        self._parsing_thread.start()

        self.parser = LevelParser()
        self.parse.connect(self.parser.parse_level)
        self.parser.parsed_level.connect(self.new_world_card)
        self.parser.moveToThread(self._parsing_thread)

        self._world_cards: list[QPixCard] = []
        self._world_cards_filtered: list[QPixCard] = []

        self._minecraft_editions: list[str] = []
        self._minecraft_versions: list[str] = []

        self.load_world_cards()

        self.lne_search_level.textChanged.connect(self.filter_cards)
        self.btn_search_level.clicked.connect(self.show_search_options)
        self.cbx_edition.currentIndexChanged.connect(self.filter_cards)
        self.cbx_version.currentIndexChanged.connect(self.filter_cards)
        self.cbx_sort.currentIndexChanged.connect(self.sort_cards)
        self.btn_sort.clicked.connect(self.toggle_sort)

    def card_clicked(self, clicked_card: QPixCard):
        for card in self._world_cards:
            card.setChecked(False)

        clicked_card.setChecked(True)
        self.level_data.emit(clicked_card.level_data)

    def load_world_cards(self):
        level_paths = minecraft.locate_levels(minecraft.save_directories())

        for path in level_paths:
            self.parse.emit(path)

    def new_world_card(self, parsed_level: ParsedLevel):
        level_data = parsed_level.level_data

        level_icon = QPixmap(QImage(parsed_level.icon_path))
        level_icon = level_icon.scaledToHeight(80)

        world_card = QPixCard(level_icon, self.wgt_search_results)
        world_card.addLabel(parsed_level.level_name)
        world_card.addLabel(parsed_level.file_name)
        world_card.addLabel(parsed_level.version)
        world_card.addLabel(parsed_level.last_played)
        world_card.setCheckable(True)
        world_card.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        world_card.clicked.connect(partial(self.card_clicked, world_card))
        world_card.level_data = level_data

        self.lyt_search_results.addWidget(world_card)
        world_card.show()

        self._world_cards.append(world_card)

        if not any(c.isalpha() for c in level_data.version):
            version = "{}.{}".format(*level_data.version.split("."))
            self.update_filters(version, level_data.edition)
        elif level_data.version == "Unknown":
            version = "Unknown"
            self.update_filters(version, level_data.edition)
        else:
            self.update_filters(edition=level_data.edition)

        self.filter_cards()

    def show_search_options(self):
        if self.btn_search_level.isChecked():
            self.scr_search_options.setVisible(True)
        else:
            self.scr_search_options.setVisible(False)

    def toggle_sort(self):
        self._sort_descending = not self._sort_descending
        if self._sort_descending:
            self.btn_sort.setIcon("sort-descending.svg")
        else:
            self.btn_sort.setIcon("sort-ascending.svg")

        self.sort_cards()

    def update_filters(
        self, version: Optional[str] = None, edition: Optional[str] = None
    ):
        if version is not None and version not in self._minecraft_versions:
            self._minecraft_versions.append(version)
            if "Unknown" not in self._minecraft_versions:
                self._minecraft_versions.sort(key=StrictVersion, reverse=True)
            else:
                self._minecraft_versions.remove("Unknown")
                self._minecraft_versions.sort(key=StrictVersion, reverse=True)
                self._minecraft_versions.append("Unknown")

            index = self._minecraft_versions.index(version) + 1

            self.cbx_version.insertItem(index, version)

        if edition is not None and edition not in self._minecraft_editions:
            self._minecraft_editions.append(edition)
            self._minecraft_editions.sort(reverse=True)

            index = self._minecraft_editions.index(edition) + 1

            self.cbx_edition.insertItem(index, edition)

    def filter_cards(self):
        search_text = self.lne_search_level.text()
        edition = self.cbx_edition.currentText()
        version = self.cbx_version.currentText()

        self._world_cards_filtered = []
        for world_card in self._world_cards:
            if (
                search_text.lower()
                in world_card.level_data.name.get_plain_text().lower()
                and (edition == "Any" or edition == world_card.level_data.edition)
                and (version == "Any" or version in world_card.level_data.version)
            ):
                self._world_cards_filtered.append(world_card)

        self.sort_cards()

    def sort_cards(self):
        sort_by = self.cbx_sort.currentText()

        if sort_by == "Name":
            self._world_cards_filtered.sort(
                key=lambda card: "".join(
                    char
                    for char in card.level_data.name.get_plain_text()
                    if char.isalnum()
                ),
                reverse=self._sort_descending,
            )
        elif sort_by == "Last Played":
            self._world_cards_filtered.sort(
                key=lambda card: card.level_data.last_played,
                reverse=self._sort_descending,
            )

        for world_card in self.wgt_search_results.children():
            if isinstance(world_card, QPixCard):
                world_card.hide()
                self.wgt_search_results.layout().removeWidget(world_card)

        for world_card in self._world_cards_filtered:
            self.wgt_search_results.layout().addWidget(world_card)
            world_card.show()

    def setupUi(self):
        # 'Search Level' field
        self.lbl_search_level = QLabel(self)
        self.lbl_search_level.setProperty("color", "on_primary")

        self.lyt_search_level = QHBoxLayout(self)

        self.frm_search_level = QFrame(self)
        self.frm_search_level.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_search_level.setFrameShadow(QFrame.Shadow.Raised)
        self.frm_search_level.setLayout(self.lyt_search_level)

        self.lne_search_level = QLineEdit(self.frm_search_level)
        self.lne_search_level.setFixedHeight(27)
        self.lne_search_level.setProperty("backgroundColor", "background")
        self.lne_search_level.setProperty("borderTop", "surface")
        self.lne_search_level.setProperty("borderLeft", "surface")
        self.lne_search_level.setProperty("borderRight", "surface")
        self.lne_search_level.setProperty("color", "on_surface")

        self.btn_search_level = AIconButton(
            "adjustments-horizontal.svg", self.frm_search_level
        )
        self.btn_search_level.setCheckable(True)
        self.btn_search_level.setFixedSize(QSize(27, 27))
        self.btn_search_level.setIconSize(QSize(15, 15))
        self.btn_search_level.setProperty("backgroundColor", "primary")

        self.lyt_search_level.addWidget(self.lne_search_level)
        self.lyt_search_level.addWidget(self.btn_search_level)
        self.lyt_search_level.setContentsMargins(0, 0, 0, 0)
        self.lyt_search_level.setSpacing(5)

        # Configure 'Search Options'
        self.scr_search_options = QScrollArea(self)
        self.wgt_search_options = QWidget(self.scr_search_options)

        self.scr_search_options.setFrameShape(QFrame.Shape.NoFrame)
        self.scr_search_options.setFrameShadow(QFrame.Shadow.Raised)
        self.scr_search_options.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scr_search_options.setProperty("backgroundColor", "background")
        self.scr_search_options.setProperty("border", "surface")
        self.scr_search_options.setProperty("borderRadiusVisible", True)
        self.scr_search_options.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scr_search_options.setVisible(False)
        self.scr_search_options.setWidgetResizable(True)
        self.scr_search_options.setWidget(self.wgt_search_options)

        self.lbl_edition = QLabel(self.wgt_search_options)
        self.lbl_edition.setProperty("color", "on_primary")

        self.cbx_edition = QComboBox(self.wgt_search_options)
        self.cbx_edition.setFixedHeight(25)

        self.lbl_version = QLabel(self.wgt_search_options)
        self.lbl_version.setProperty("color", "on_primary")

        self.cbx_version = QComboBox(self.wgt_search_options)
        self.cbx_version.setFixedHeight(25)

        self.lbl_sort = QLabel(self.wgt_search_options)
        self.lbl_sort.setProperty("color", "on_primary")

        self.lyt_sort = QHBoxLayout(self)

        self.frm_sort = QFrame(self)
        self.frm_sort.setFrameShape(QFrame.Shape.NoFrame)
        self.frm_sort.setFrameShadow(QFrame.Shadow.Raised)
        self.frm_sort.setLayout(self.lyt_sort)

        self.cbx_sort = QComboBox(self.wgt_search_options)
        self.cbx_sort.setFixedHeight(25)

        self.btn_sort = AIconButton("sort-descending.svg", self.frm_sort)
        self.btn_sort.setFixedSize(QSize(27, 27))
        self.btn_sort.setIconSize(QSize(15, 15))
        self.btn_sort.setProperty("backgroundColor", "primary")

        self.lyt_sort.addWidget(self.cbx_sort)
        self.lyt_sort.addWidget(self.btn_sort)
        self.lyt_sort.setContentsMargins(0, 0, 0, 0)
        self.lyt_sort.setSpacing(5)

        self.lyt_search_options = QVBoxLayout(self.scr_search_options)
        self.lyt_search_options.addWidget(self.lbl_edition)
        self.lyt_search_options.addWidget(self.cbx_edition)
        self.lyt_search_options.addSpacing(5)
        self.lyt_search_options.addWidget(self.lbl_version)
        self.lyt_search_options.addWidget(self.cbx_version)
        self.lyt_search_options.addSpacing(5)
        self.lyt_search_options.addWidget(self.lbl_sort)
        self.lyt_search_options.addWidget(self.frm_sort)
        self.lyt_search_options.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lyt_search_options.setContentsMargins(7, 7, 7, 7)

        self.wgt_search_options.setLayout(self.lyt_search_options)
        self.wgt_search_options.setProperty("backgroundColor", "background")

        self.scr_search_options.setMaximumHeight(
            self.wgt_search_options.sizeHint().height()
        )

        # Configure 'Search Results'
        self.scr_search_results = QScrollArea(self)
        self.wgt_search_results = QWidget(self.scr_search_results)

        self.scr_search_results.setFrameShape(QFrame.Shape.NoFrame)
        self.scr_search_results.setFrameShadow(QFrame.Shadow.Raised)
        self.scr_search_results.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scr_search_results.setProperty("backgroundColor", "background")
        self.scr_search_results.setProperty("border", "surface")
        self.scr_search_results.setProperty("borderRadiusVisible", True)
        self.scr_search_results.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scr_search_results.setWidgetResizable(True)
        self.scr_search_results.setWidget(self.wgt_search_results)

        self.lyt_search_results = QVBoxLayout(self.scr_search_results)
        self.lyt_search_results.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lyt_search_results.setContentsMargins(5, 5, 5, 5)

        self.wgt_search_results.setLayout(self.lyt_search_results)
        self.wgt_search_results.setProperty("backgroundColor", "background")

        # Configure 'Page' layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_search_level)
        layout.addWidget(self.frm_search_level)
        layout.addWidget(self.scr_search_options)
        layout.addWidget(self.scr_search_results)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(layout)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.lbl_search_level.setText(QCoreApplication.translate("NewProjectTypePage", "Search", None))
        self.lbl_edition.setText(QCoreApplication.translate("NewProjectTypePage", "Minecraft Edition", None))
        self.lbl_version.setText(QCoreApplication.translate("NewProjectTypePage", "Minecraft Version", None))
        self.lbl_sort.setText(QCoreApplication.translate("NewProjectTypePage", "Sort Order", None))
        # fmt: on
