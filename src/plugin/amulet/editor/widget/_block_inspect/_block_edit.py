import logging

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QWidget,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
)

from amulet.nbt import read_snbt, ByteTag, ShortTag, IntTag, LongTag, StringTag

from amulet.core.block import Block, BlockStack
from amulet.core.block_entity import BlockEntity
from amulet.core.version import VersionNumber

from amulet.game import get_game_platforms, get_game_versions, get_game_version
from amulet.game.abc import GameVersion

log = logging.getLogger(__name__)


class PropertySelect(QWidget):
    def __init__(self, name: str, values: list[str], index: int) -> None:
        super().__init__()

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._name = QLabel(text=name)
        self._layout.addWidget(self._name)

        self._property = QComboBox()
        self._property.addItems(values)
        self._property.setCurrentIndex(index)
        self._layout.addWidget(self._property)

    def get_name(self) -> str:
        return self._name.text()

    def set_name(self, value: str) -> None:
        self._name.setText(value)

    def get_value(self) -> ByteTag | ShortTag | IntTag | LongTag | StringTag:
        text = self._property.currentText()
        nbt = read_snbt(text)
        if isinstance(nbt, (ByteTag, ShortTag, IntTag, LongTag, StringTag)):
            return nbt
        raise RuntimeError(
            f"Property value must be a ByteTag, ShortTag, IntTag, LongTag or StringTag, got {nbt}"
        )

    def set_value(
        self, value: ByteTag | ShortTag | IntTag | LongTag | StringTag
    ) -> None:
        snbt = value.to_snbt()
        index = self._property.findText(snbt)
        if index != -1:
            self._property.setCurrentIndex(index)


class BlockEdit(QWidget):
    # def __init__(self, is_extra_block: bool) -> None:
    def __init__(self) -> None:
        super().__init__()
        # self._is_extra_block = is_extra_block

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._platform_select = QComboBox()
        self._layout.addWidget(self._platform_select)

        self._versions_select = QComboBox()
        self._layout.addWidget(self._versions_select)

        self._namespace_select = QComboBox()
        self._namespace_select.setEditable(True)
        self._layout.addWidget(self._namespace_select)

        self._base_name_select = QComboBox()
        self._base_name_select.setEditable(True)
        self._layout.addWidget(self._base_name_select)

        self._properties_layout_container = QHBoxLayout()
        self._layout.addLayout(self._properties_layout_container)

        self._properties_layout_container.addSpacing(20)
        self._properties_layout = QVBoxLayout()
        self._properties_layout_container.addLayout(self._properties_layout)

        # self._snbt_input = QTextEdit()
        # self._layout.addWidget(self._snbt_input)
        # self._snbt_input.setVisible(not self._is_extra_block)

        self._layout.addStretch(1)

        self._platform_select.currentIndexChanged.connect(self._on_platform_change)
        self._versions_select.currentIndexChanged.connect(self._on_version_change)
        self._namespace_select.currentTextChanged.connect(self._on_namespace_change)
        self._base_name_select.currentTextChanged.connect(self._on_base_name_change)

        platforms = [
            platform for platform in get_game_platforms() if platform != "universal"
        ]
        self._platform_select.addItems(platforms)

    def get_block(self) -> Block:
        return Block(
            self.get_platform(),
            self.get_block_version(),
            self.get_namespace(),
            self.get_base_name(),
            self.get_properties(),
        )

    def set_block(self, block: Block) -> None:
        with QSignalBlocker(self._platform_select):
            self.set_platform(block.platform)
        self._update_version()
        with QSignalBlocker(self._versions_select):
            self.set_version(block.version)
        game_version = self._get_game_version()
        self._update_namespace(game_version)
        with QSignalBlocker(self._namespace_select):
            self.set_namespace(block.namespace)
        self._update_base_name(game_version)
        with QSignalBlocker(self._base_name_select):
            self.set_base_name(block.base_name)
        self._update_block(game_version)
        self.set_properties(block.properties)

    def get_platform(self) -> str:
        return self._platform_select.currentText()

    def set_platform(self, platform: str) -> None:
        index = self._platform_select.findText(platform)
        if index == -1:
            raise RuntimeError(f"Platform {platform} not found.")
        self._platform_select.setCurrentIndex(index)

    def get_block_version(self) -> VersionNumber:
        return self._versions_select.currentData()

    def set_version(self, version: VersionNumber) -> None:
        index = next(
            (
                i
                for i in range(self._versions_select.count())
                if get_game_version(
                    self.get_platform(), self._versions_select.itemData(i)
                ).supports_version(self.get_platform(), version)
            ),
            -1,
        )
        if index == -1:
            self._versions_select.addItem(str(version), version)
            index = self._versions_select.findData(version)
        self._versions_select.setCurrentIndex(index)

    def get_namespace(self) -> str:
        return self._namespace_select.currentText()

    def set_namespace(self, namespace: str) -> None:
        index = self._namespace_select.findData(namespace)
        if index == -1:
            self._namespace_select.setCurrentText(namespace)
        else:
            self._namespace_select.setCurrentIndex(index)

    def get_base_name(self) -> str:
        return self._base_name_select.currentText()

    def set_base_name(self, base_name: str) -> None:
        index = self._base_name_select.findData(base_name)
        if index == -1:
            self._base_name_select.setCurrentText(base_name)
        else:
            self._base_name_select.setCurrentIndex(index)

    def _get_property_widgets(self) -> list[PropertySelect]:
        widgets: list[PropertySelect] = []
        for i in range(0, self._properties_layout.count()):
            item = self._properties_layout.itemAt(i)
            if item is None:
                raise RuntimeError
            widget = item.widget()
            if not isinstance(widget, PropertySelect):
                raise RuntimeError
            widgets.append(widget)
        return widgets

    def get_properties(self) -> dict[str, Block.PropertyValue]:
        return {
            widget.get_name(): widget.get_value()
            for widget in self._get_property_widgets()
        }

    def set_properties(self, properties: dict[str, Block.PropertyValue]) -> None:
        widgets: dict[str, PropertySelect] = {
            widget.get_name(): widget for widget in self._get_property_widgets()
        }
        for name, value in properties.items():
            widget = widgets.get(name)
            if widget is None:
                continue
            if value is not None:
                widget.set_value(value)
            else:
                # TODO: populate the GUI with this somehow?
                continue

    def _get_game_version(self) -> GameVersion:
        return get_game_version(self.get_platform(), self.get_block_version())

    def _on_platform_change(self) -> None:
        self._update_version_recursive()

    def _update_version(self) -> None:
        log.debug("Updating version")
        with QSignalBlocker(self._versions_select):
            self._versions_select.clear()

            def version_sort(v: GameVersion) -> VersionNumber:
                return v.min_semantic_version

            for version in sorted(
                get_game_versions(self.get_platform()),
                key=version_sort,
                reverse=True,
            ):
                if version.min_semantic_version == version.max_known_semantic_version:
                    label = f"{version.min_semantic_version}"
                else:
                    label = f"{version.min_semantic_version} - {version.max_known_semantic_version}"
                if version.min_block_version == version.max_known_block_version:
                    label += f", {version.min_block_version}"
                else:
                    label += f", {version.min_block_version} - {version.max_known_block_version}"
                self._versions_select.addItem(label, version.min_block_version)
            self._versions_select.setCurrentIndex(0)

    def _update_version_recursive(self) -> None:
        self._update_version()
        self._update_namespace_recursive(self._get_game_version())

    def _on_version_change(self) -> None:
        self._update_namespace_recursive(self._get_game_version())

    def _update_namespace(self, version: GameVersion) -> None:
        log.debug("Updating namespace")
        with QSignalBlocker(self._namespace_select):
            self._namespace_select.clear()
            self._namespace_select.addItems(sorted(version.block.namespaces()))
            self._namespace_select.setCurrentIndex(0)

    def _update_namespace_recursive(self, version: GameVersion) -> None:
        self._update_namespace(version)
        self._update_base_name_recursive(version)

    def _on_namespace_change(self) -> None:
        self._update_base_name_recursive(self._get_game_version())

    def _update_base_name(self, version: GameVersion) -> None:
        log.debug("Updating base name")
        with QSignalBlocker(self._base_name_select):
            self._base_name_select.clear()
            self._base_name_select.addItems(
                sorted(version.block.base_names(self.get_namespace()))
            )
            self._base_name_select.setCurrentIndex(0)

    def _update_base_name_recursive(self, version: GameVersion) -> None:
        self._update_base_name(version)
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
                self.get_namespace(), self.get_base_name()
            )
        except KeyError:
            pass
        else:
            properties = spec.properties
            for property_index, (name, prop_spec) in enumerate(properties.items()):
                states: list[str] = []
                index = 0
                for state_index, state in enumerate(prop_spec.states):
                    states.append(state.to_snbt())
                    if state == prop_spec.default:
                        index = state_index

                property_widget = PropertySelect(name, states, index)
                self._properties_layout.addWidget(property_widget)

            # if self._is_extra_block or spec.nbt is None:
            #     self._snbt_input.hide()
            #     self._snbt_input.clear()
            # else:
            #     self._snbt_input.show()
            #     self._snbt_input.setText(spec.nbt.snbt)


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

    widget = BlockEdit()
    layout_2.addWidget(widget)
    layout_2.addStretch(1)

    window.show()

    app.exec()


if __name__ == "__main__":
    main()
