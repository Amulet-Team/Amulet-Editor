from functools import partial
from typing import Any, Callable, Optional, Protocol

from amulet_editor.models.widgets import QIconButton
from PySide6.QtCore import QCoreApplication, QSize, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SearchItem(Protocol):
    """Item should be a `QPushButton` that can be constructed using only the
    `result` emitted from a paired `DataParser`"""

    @property
    def data(self) -> Any:
        ...


class DataParser(Protocol):
    """Parser must be a subclass of `QObject` for `Signal` and `Slot` compatability."""

    result: Signal

    def parse(self, raw_data: Any) -> None:
        """This method will emit the parsed data from the `result` Signal."""
        ...

    def moveToThread(self, thread: QThread) -> None:
        """Changes the thread affinity for this object and its children."""
        ...


class SearchPanel(QWidget):

    data = Signal(object)
    raw_data = Signal(object)

    def __init__(self) -> None:
        super().__init__()

        self.setupUi()

        self.btng_items = QButtonGroup()
        self.btng_items.setExclusive(True)

        self.cbx_sort: Optional[QComboBox] = None
        self.btn_sort: Optional[QIconButton] = None
        self.sort_descending = True

        self.parser: Optional[DataParser] = None
        self.parsing_thread = QThread()
        self.parsing_await = 0

        self.search_item: Optional[Callable[[Any], SearchItem]] = None

        self.filters: list[Callable] = []
        self.sorters: dict[str, Callable] = {"Search": None}

        self.items: list[QPushButton] = []
        self.filtered_items: list[QPushButton] = []

        self.lne_search_bar.textChanged.connect(self.filter_items)
        self.btn_search_options.clicked.connect(self.show_search_options)
        self.cbx_sort.currentIndexChanged.connect(self.sort_items)
        self.btn_sort.clicked.connect(self.toggle_sort)

    def item_clicked(self, item: SearchItem):
        self.data.emit(item.data)

    # def load_world_cards(self) -> None:
    #     level_paths = minecraft.locate_levels(minecraft.save_directories())

    #     if not any(c.isalpha() for c in level_data.version):
    #         version = "{}.{}".format(*level_data.version.split("."))
    #         self.update_filters(version, level_data.edition)
    #     elif level_data.version == "Unknown":
    #         version = "Unknown"
    #         self.update_filters(version, level_data.edition)
    #     else:
    #         self.update_filters(edition=level_data.edition)

    #     self.filter_items()

    def show_search_options(self) -> None:
        self.scr_search_options.setVisible(self.btn_search_options.isChecked())

    def toggle_sort(self) -> None:
        self.sort_descending = not self.sort_descending
        if self.sort_descending:
            self.btn_sort.setIcon("sort-descending.svg")
        else:
            self.btn_sort.setIcon("sort-ascending.svg")

        self.sort_items()

    def create_item(self, __raw_data: Any, /) -> None:
        self.raw_data.emit(__raw_data)

    def _create_item(self, data: Any) -> None:
        # if version is not None and version not in self.minecraft_versions:
        #     self.minecraft_versions.append(version)
        #     if "Unknown" not in self.minecraft_versions:
        #         self.minecraft_versions.sort(key=StrictVersion, reverse=True)
        #     else:
        #         self.minecraft_versions.remove("Unknown")
        #         self.minecraft_versions.sort(key=StrictVersion, reverse=True)
        #         self.minecraft_versions.append("Unknown")

        #     index = self.minecraft_versions.index(version) + 1

        #     self.cbx_version.insertItem(index, version)

        # if edition is not None and edition not in self.minecraft_editions:
        #     self.minecraft_editions.append(edition)
        #     self.minecraft_editions.sort(reverse=True)

        #     index = self.minecraft_editions.index(edition) + 1

        #     self.cbx_edition.insertItem(index, edition)
        item = self.search_item(data)
        self.btng_items.addButton(item)

        self.items.append(item)
        self.filter_items()

    def filter_items(self) -> None:
        # search_text = self.lne_search_bar.text()
        # edition = self.cbx_edition.currentText()
        # version = self.cbx_version.currentText()

        # self.world_items_filtered = []
        # for world_card in self.world_items:
        #     if (
        #         search_text.lower()
        #         in world_card.level_data.name.get_plain_text().lower()
        #         and (edition == "Any" or edition == world_card.level_data.edition)
        #         and (version == "Any" or version in world_card.level_data.version)
        #     ):
        #         self.world_items_filtered.append(world_card)

        def multi_filter(filters, iterable):
            if not filters:
                return iterable
            return multi_filter(filters[1:], filter(filters[0], iterable))

        self.filtered_items = multi_filter(self.filters, self.items)

        self.sort_items()

    def sort_items(self):
        sort_by = self.cbx_sort.currentText()

        self.filtered_items = sorted(
            self.filtered_items,
            key=self.sorters.get(sort_by, None),
            reverse=self.sort_descending,
        )

        # if sort_by == "Name":
        #     self.world_items_filtered.sort(
        #         key=lambda card: "".join(
        #             char
        #             for char in card.level_data.name.get_plain_text()
        #             if char.isalnum()
        #         ),
        #         reverse=self.sort_descending,
        #     )
        # elif sort_by == "Last Played":
        #     self.world_items_filtered.sort(
        #         key=lambda card: card.level_data.last_played,
        #         reverse=self.sort_descending,
        #     )

        for item in self.wgt_search_results.children():
            if isinstance(item, QPushButton):
                item.hide()
                self.wgt_search_results.layout().removeWidget(item)

        for item in self.filtered_items:
            self.wgt_search_results.layout().addWidget(item)
            item.show()

    def setParser(self, parser: DataParser) -> None:
        self.parser = parser
        self.raw_data.connect(self.parser.parse)
        self.parser.result.connect(self._create_item)
        self.parser.moveToThread(self.parsing_thread)

    def setSearchItem(self, search_item: Callable[[Any], SearchItem]) -> None:
        self.search_item = search_item

    def addFilter(
        self,
        label: str,
        options: list[str],
        __filter: Callable[[Callable[[], str], Any], bool],
    ) -> None:
        lbl_filter = QLabel(label, self.wgt_search_options)
        lbl_filter.setProperty("color", "on_primary")

        cbx_filter = QComboBox(self.wgt_search_options)
        cbx_filter.setFixedHeight(25)
        cbx_filter.currentIndexChanged.connect(self.filter_items)

        for option in options:
            cbx_filter.addItem(option)

        self.lyt_search_options.addSpacing(5)
        self.lyt_search_options.addWidget(lbl_filter)
        self.lyt_search_options.addWidget(cbx_filter)

        # Add four to ensure max height is large enough to not need scrollbar
        self.scr_search_options.setMaximumHeight(
            self.wgt_search_options.sizeHint().height() + 4
        )

        self.filters.append(partial(__filter, cbx_filter.currentText))

    def addSorter(self, option: str, __sorter: Callable[[list[Any]], int]) -> None:
        if self.cbx_sort is None:
            lbl_sort = QLabel(self.wgt_search_options)
            lbl_sort.setProperty("color", "on_primary")
            lbl_sort.setText(
                QCoreApplication.translate("NewProjectTypePage", "Sort Order", None)
            )

            lyt_sort = QHBoxLayout(self)

            frm_sort = QFrame(self)
            frm_sort.setFrameShape(QFrame.NoFrame)
            frm_sort.setFrameShadow(QFrame.Raised)
            frm_sort.setLayout(lyt_sort)
            frm_sort.setProperty("border", "surface")
            frm_sort.setProperty("borderLeft", "none")
            frm_sort.setProperty("borderRight", "none")
            frm_sort.setProperty("borderTop", "none")

            self.cbx_sort = QComboBox(self.wgt_search_options)
            self.cbx_sort.setFixedHeight(25)
            self.cbx_sort.currentIndexChanged.connect(self.sort_items)

            self.btn_sort = QIconButton(frm_sort)
            self.btn_sort.setFixedSize(QSize(27, 27))
            self.btn_sort.setIcon("sort-descending.svg")
            self.btn_sort.setIconSize(QSize(15, 15))
            self.btn_sort.setProperty("backgroundColor", "primary")

            lyt_sort.addWidget(self.cbx_sort)
            lyt_sort.addWidget(self.btn_sort)
            lyt_sort.setContentsMargins(0, 0, 0, 10)
            lyt_sort.setSpacing(5)

            self.lyt_search_options.insertWidget(0, lbl_sort)
            self.lyt_search_options.insertWidget(1, frm_sort)
            self.lyt_search_options.addSpacing(5)

            # Add four to ensure max height is large enough to not need scrollbar
            self.scr_search_options.setMaximumHeight(
                self.wgt_search_options.sizeHint().height() + 4
            )

        self.cbx_sort.addItem(option)
        self.sorters.update({option: __sorter})

    def addParser(self, parser: DataParser) -> None:
        if self.parser is not None:
            raise

        self.parser = parser
        self.raw_data.connect(self.parser.parse)
        self.parser.result.connect(self.new_world_card)
        self.parser.moveToThread(self.parsing_thread)

    def setupUi(self):
        # Search controls
        self.lbl_search = QLabel(self)
        self.lbl_search.setProperty("color", "on_primary")

        self.lyt_search = QHBoxLayout(self)

        self.frm_search = QFrame(self)
        self.frm_search.setFrameShape(QFrame.NoFrame)
        self.frm_search.setFrameShadow(QFrame.Raised)
        self.frm_search.setLayout(self.lyt_search)

        self.lne_search_bar = QLineEdit(self.frm_search)
        self.lne_search_bar.setFixedHeight(27)
        self.lne_search_bar.setProperty("backgroundColor", "background")
        self.lne_search_bar.setProperty("borderTop", "surface")
        self.lne_search_bar.setProperty("borderLeft", "surface")
        self.lne_search_bar.setProperty("borderRight", "surface")
        self.lne_search_bar.setProperty("color", "on_surface")

        self.btn_search_options = QIconButton(self.frm_search)
        self.btn_search_options.setCheckable(True)
        self.btn_search_options.setFixedSize(QSize(27, 27))
        self.btn_search_options.setIcon("adjustments-horizontal.svg")
        self.btn_search_options.setIconSize(QSize(15, 15))
        self.btn_search_options.setProperty("backgroundColor", "primary")

        self.lyt_search.addWidget(self.lne_search_bar)
        self.lyt_search.addWidget(self.btn_search_options)
        self.lyt_search.setContentsMargins(0, 0, 0, 0)
        self.lyt_search.setSpacing(5)

        # Search options
        self.scr_search_options = QScrollArea(self)
        self.wgt_search_options = QWidget(self.scr_search_options)

        self.scr_search_options.setFrameShape(QFrame.NoFrame)
        self.scr_search_options.setFrameShadow(QFrame.Raised)
        self.scr_search_options.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scr_search_options.setProperty("backgroundColor", "background")
        self.scr_search_options.setProperty("border", "surface")
        self.scr_search_options.setProperty("borderRadiusVisible", True)
        self.scr_search_options.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scr_search_options.setVisible(False)
        self.scr_search_options.setWidgetResizable(True)
        self.scr_search_options.setWidget(self.wgt_search_options)

        self.lyt_search_options = QVBoxLayout(self.scr_search_options)
        self.lyt_search_options.setAlignment(Qt.AlignTop)

        self.wgt_search_options.setLayout(self.lyt_search_options)
        self.wgt_search_options.setProperty("backgroundColor", "background")

        # Search results
        self.scr_search_results = QScrollArea(self)
        self.wgt_search_results = QWidget(self.scr_search_results)

        self.scr_search_results.setFrameShape(QFrame.NoFrame)
        self.scr_search_results.setFrameShadow(QFrame.Raised)
        self.scr_search_results.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scr_search_results.setProperty("backgroundColor", "background")
        self.scr_search_results.setProperty("border", "surface")
        self.scr_search_results.setProperty("borderRadiusVisible", True)
        self.scr_search_results.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scr_search_results.setWidgetResizable(True)
        self.scr_search_results.setWidget(self.wgt_search_results)

        self.lyt_search_results = QVBoxLayout(self.scr_search_results)
        self.lyt_search_results.setAlignment(Qt.AlignTop)

        self.wgt_search_results.setLayout(self.lyt_search_results)
        self.wgt_search_results.setProperty("backgroundColor", "background")

        # Page layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_search)
        layout.addWidget(self.frm_search)
        layout.addWidget(self.scr_search_options)
        layout.addWidget(self.scr_search_results)
        layout.setAlignment(Qt.AlignTop)

        self.setLayout(layout)
        self.retranslateUi()

    def retranslateUi(self):
        # fmt: off
        self.lbl_search.setText(QCoreApplication.translate("NewProjectTypePage", "Search", None))
        # fmt: on
