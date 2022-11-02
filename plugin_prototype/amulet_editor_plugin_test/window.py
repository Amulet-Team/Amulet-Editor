from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, Slot
from PySide6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QWidget, QLabel, QCheckBox

from .plugin_manager import PluginData, PluginState, PluginUID
from .thread import Thread

if TYPE_CHECKING:
    from .plugin_api import AppPrivateAPI


class MainWindow(QMainWindow):
    __plugin_map: dict[PluginUID, tuple[QCheckBox, QLabel]] = {}

    def __init__(self, api: AppPrivateAPI):
        super().__init__()
        self.__api = api
        self.setObjectName("MainWindow")
        self.resize(875, 702)
        self.centralwidget = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.__init_table(self.centralwidget, self.verticalLayout)
        for plugin_data, plugin_state in self.__api.iter_plugins():
            self.__add_row(plugin_data, plugin_state)
        self.__api.plugin_state_change.connect(self.__on_plugin_state_change)
        self.setCentralWidget(self.centralwidget)
        self.translate()
        QMetaObject.connectSlotsByName(self)

    def __init_table(self, parent, layout):
        self.__plugin_map = {}
        self.gridLayout = QGridLayout()
        layout.addLayout(self.gridLayout)
        self.plugin_name_label = QLabel(parent)
        self.gridLayout.addWidget(self.plugin_name_label, 0, 0)
        self.plugin_id_label = QLabel(parent)
        self.gridLayout.addWidget(self.plugin_id_label, 0, 1)
        self.plugin_version_label = QLabel(parent)
        self.gridLayout.addWidget(self.plugin_version_label, 0, 2)
        self.plugin_enabled_label = QLabel(parent)
        self.gridLayout.addWidget(self.plugin_enabled_label, 0, 3)
        self.plugin_status_label = QLabel(parent)
        self.gridLayout.addWidget(self.plugin_status_label, 0, 4)

    def __add_row(self, plugin_data: PluginData, plugin_state: PluginState):
        index = len(self.__plugin_map) + 1

        # plugin name
        name_item = QLabel(self.centralwidget)
        name_item.setText(plugin_data.name)
        self.gridLayout.addWidget(name_item, index, 0)

        # plugin id
        id_item = QLabel(self.centralwidget)
        id_item.setText(plugin_data.uid.identifier)
        self.gridLayout.addWidget(id_item, index, 1)

        # plugin version
        version_item = QLabel(self.centralwidget)
        version_item.setText(str(plugin_data.uid.version))
        self.gridLayout.addWidget(version_item, index, 2)

        # enabled checkbox
        enabled_item = QCheckBox(self.centralwidget)
        enabled_item.setChecked(bool(plugin_state))
        self.gridLayout.addWidget(enabled_item, index, 3)

        # plugin state
        state_item = QLabel(self.centralwidget)
        self.__set_enabled_state(state_item, plugin_state)
        self.gridLayout.addWidget(state_item, index, 4)

        self.__plugin_map[plugin_data.uid] = (enabled_item, state_item)

        def on_change(state: int):
            if state == Qt.Unchecked:
                Thread(target=lambda : self.__api.disable_plugin(plugin_data.uid)).start()
            else:
                Thread(target=lambda: self.__api.enable_plugin(plugin_data.uid)).start()

        enabled_item.stateChanged.connect(on_change)

        self.setFixedSize(self.width(), self.verticalLayout.sizeHint().height())

    @Slot(PluginUID, PluginState)
    def __on_plugin_state_change(self, plugin_uid: PluginUID, plugin_state: PluginState):
        enabled_item, state_item = self.__plugin_map[plugin_uid]
        enabled_state = bool(plugin_state)
        if enabled_item.isChecked() != enabled_state:
            enabled_item.setChecked(enabled_state)
        self.__set_enabled_state(state_item, plugin_state)

    def __set_enabled_state(self, item: QLabel, plugin_state: PluginState):
        text = {
            PluginState.Disabled: "Disabled",
            PluginState.Inactive: "Inactive",
            PluginState.Enabled: "Enabled"
        }[plugin_state]
        item.setText(text)

    def translate(self):
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.plugin_name_label.setText(QCoreApplication.translate("MainWindow", "Plugin Name", None))
        self.plugin_id_label.setText(QCoreApplication.translate("MainWindow", "Plugin Identifier", None))
        self.plugin_version_label.setText(QCoreApplication.translate("MainWindow", "Plugin Version", None))
        self.plugin_enabled_label.setText(QCoreApplication.translate("MainWindow", "Plugin Enabled", None))
        self.plugin_status_label.setText(QCoreApplication.translate("MainWindow", "Plugin State", None))
