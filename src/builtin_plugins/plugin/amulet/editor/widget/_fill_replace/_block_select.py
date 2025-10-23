import logging

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QWidget,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QTextEdit,
)

from amulet.game import get_game_platforms, get_game_versions, get_game_version
from amulet.game.abc import GameVersion

log = logging.getLogger(__name__)


class BlockSelect(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._platform_select = QComboBox()
        self._layout.addWidget(self._platform_select)

        self._versions_select = QComboBox()
        self._layout.addWidget(self._versions_select)

        self._namespace_select = QComboBox()
        self._layout.addWidget(self._namespace_select)

        self._base_name_select = QComboBox()
        self._base_name_select.setEditable(True)
        self._layout.addWidget(self._base_name_select)

        self._properties_layout_container = QHBoxLayout()
        self._layout.addLayout(self._properties_layout_container)

        self._properties_layout_container.addSpacing(20)
        self._properties_layout = QGridLayout()
        self._properties_layout_container.addLayout(self._properties_layout)

        self._snbt_input = QTextEdit()
        self._layout.addWidget(self._snbt_input)

        self._platform_select.currentIndexChanged.connect(self._on_platform_change)
        self._versions_select.currentIndexChanged.connect(self._on_version_change)
        self._namespace_select.currentTextChanged.connect(self._on_namespace_change)
        self._base_name_select.currentTextChanged.connect(self._on_base_name_change)

        platforms = [
            platform for platform in get_game_platforms() if platform != "universal"
        ]
        self._platform_select.addItems(platforms)

    def _get_game_version(self) -> GameVersion:
        return get_game_version(
            self._platform_select.currentText(), self._versions_select.currentData()
        )

    def _on_platform_change(self) -> None:
        self._update_version()

    def _update_version(self) -> None:
        log.debug("Updating version")
        with QSignalBlocker(self._versions_select):
            self._versions_select.clear()
            for version in sorted(
                game_version.min_version
                for game_version in get_game_versions(
                    self._platform_select.currentText()
                )
            ):
                self._versions_select.addItem(str(version), version)
            self._versions_select.setCurrentIndex(self._versions_select.count() - 1)
        self._update_namespace(self._get_game_version())

    def _on_version_change(self) -> None:
        self._update_namespace(self._get_game_version())

    def _update_namespace(self, version: GameVersion) -> None:
        log.debug("Updating namespace")
        with QSignalBlocker(self._namespace_select):
            self._namespace_select.clear()
            self._namespace_select.addItems(sorted(version.block.namespaces()))
            self._namespace_select.setCurrentIndex(0)
        self._update_base_name(version)

    def _on_namespace_change(self) -> None:
        self._update_base_name(self._get_game_version())

    def _update_base_name(self, version: GameVersion) -> None:
        log.debug("Updating base name")
        with QSignalBlocker(self._base_name_select):
            self._base_name_select.clear()
            self._base_name_select.addItems(
                sorted(version.block.base_names(self._namespace_select.currentText()))
            )
            self._base_name_select.setCurrentIndex(0)
        self._update_block(version)

    def _on_base_name_change(self) -> None:
        self._update_block(self._get_game_version())

    def _update_block(self, version: GameVersion) -> None:
        log.debug("Updating block")
        while (item := self._properties_layout.takeAt(0)) is not None:
            if (widget := item.widget()) is not None:
                widget.deleteLater()
        try:
            spec = version.block.get_specification(
                self._namespace_select.currentText(),
                self._base_name_select.currentText(),
            )
        except KeyError:
            pass
        else:
            properties = spec.properties
            for property_index, (name, prop_spec) in enumerate(properties.items()):
                self._properties_layout.addWidget(QLabel(name), property_index, 0)
                combo = QComboBox()
                for state_index, state in enumerate(prop_spec.states):
                    combo.addItem(state.to_snbt(), state)
                    if state == prop_spec.default:
                        combo.setCurrentIndex(state_index)
                self._properties_layout.addWidget(combo, property_index, 1)

            if spec.nbt is None:
                self._snbt_input.hide()
                self._snbt_input.clear()
            else:
                self._snbt_input.show()
                self._snbt_input.setText(spec.nbt.snbt)


def main() -> None:
    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG, force=True)

    app = QApplication()

    window = QWidget()
    layout_1 = QVBoxLayout(window)
    layout_1.setContentsMargins(0, 0, 0, 0)
    layout_2 = QHBoxLayout()
    layout_2.setContentsMargins(0, 0, 0, 0)
    layout_1.addLayout(layout_2)
    layout_1.addStretch(1)

    widget = BlockSelect()
    layout_2.addWidget(widget)
    layout_2.addStretch(1)

    window.show()

    app.exec()


if __name__ == "__main__":
    main()
