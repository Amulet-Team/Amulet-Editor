from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, Slot
from PySide6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PySide6.QtGui import QColor

from .plugin_manager import PluginData, PluginState, PluginUID

if TYPE_CHECKING:
    from .plugin_api import AppPrivateAPI


EnabledState = {
    PluginState.Disabled: Qt.Unchecked,
    PluginState.Inactive: Qt.Checked,
    PluginState.Enabled: Qt.Checked
}


class TableCheckboxItem(QTableWidgetItem):
    plugin_data: PluginData

    def __init__(self, plugin_data: PluginData):
        super().__init__()
        self.plugin_data = plugin_data


class MainWindow(QMainWindow):
    __plugin_map: dict[PluginUID, tuple[TableCheckboxItem, QTableWidgetItem]] = {}

    def __init__(self, api: AppPrivateAPI):
        super().__init__()
        self.__api = api
        self.setObjectName("MainWindow")
        self.resize(875, 702)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.__init_table(self.centralwidget, self.verticalLayout)
        for plugin_data, plugin_state in self.__api.iter_plugins():
            self.__add_row(plugin_data, plugin_state)
        self.__api.plugin_state_change.connect(self.__on_plugin_state_change)
        self.setCentralWidget(self.centralwidget)
        self.translate()
        QMetaObject.connectSlotsByName(self)

    def __init_table(self, parent, layout):
        self.__plugin_map = {}
        self.tableWidget = QTableWidget(parent)
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem())
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem())
        self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem())
        self.tableWidget.setHorizontalHeaderItem(3, QTableWidgetItem())
        self.tableWidget.setHorizontalHeaderItem(4, QTableWidgetItem())
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.itemChanged.connect(self.__on_change)
        layout.addWidget(self.tableWidget)

    def __on_change(self, item: QTableWidgetItem):
        if isinstance(item, TableCheckboxItem):
            if item.checkState() == Qt.Checked:
                self.__api.enable_plugin(item.plugin_data.uid)
            else:
                self.__api.disable_plugin(item.plugin_data.uid)

    def __add_row(self, plugin_data: PluginData, plugin_state: PluginState):
        index = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(index + 1)
        self.tableWidget.setVerticalHeaderItem(index, QTableWidgetItem())

        # plugin name
        name_item = QTableWidgetItem()
        name_item.setText(plugin_data.name)
        self.tableWidget.setItem(index, 0, name_item)

        # plugin id
        id_item = QTableWidgetItem()
        id_item.setText(plugin_data.uid.identifier)
        self.tableWidget.setItem(index, 1, id_item)

        # plugin version
        version_item = QTableWidgetItem()
        version_item.setText(str(plugin_data.uid.version))
        self.tableWidget.setItem(index, 2, version_item)

        # enabled checkbox
        enabled_item = TableCheckboxItem(plugin_data)
        enabled_item.setCheckState(EnabledState[plugin_state])
        self.tableWidget.setItem(index, 3, enabled_item)

        # plugin state
        state_item = QTableWidgetItem()
        self.__set_enabled_state(state_item, plugin_state)
        self.tableWidget.setItem(index, 4, state_item)

        self.__plugin_map[plugin_data.uid] = (enabled_item, state_item)

    @Slot(PluginUID, PluginState)
    def __on_plugin_state_change(self, plugin_uid: PluginUID, plugin_state: PluginState):
        print("state change", plugin_uid, plugin_state)
        enabled_item, state_item = self.__plugin_map[plugin_uid]
        enabled_item.setCheckState(EnabledState[plugin_state])
        self.__set_enabled_state(state_item, plugin_state)

    def __set_enabled_state(self, item: QTableWidgetItem, plugin_state: PluginState):
        text, colour = {
            PluginState.Disabled: ("Disabled", QColor(255, 0, 0)),
            PluginState.Inactive: ("Inactive", QColor(255, 255, 0)),
            PluginState.Enabled: ("Enabled", QColor(0, 255, 0))
        }[plugin_state]
        item.setText(text)
        item.setBackground(colour)

    def translate(self):
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.tableWidget.horizontalHeaderItem(0).setText(QCoreApplication.translate("MainWindow", "Plugin Name", None))
        self.tableWidget.horizontalHeaderItem(1).setText(QCoreApplication.translate("MainWindow", "Plugin Identifier", None))
        self.tableWidget.horizontalHeaderItem(2).setText(QCoreApplication.translate("MainWindow", "Plugin Version", None))
        self.tableWidget.horizontalHeaderItem(3).setText(QCoreApplication.translate("MainWindow", "Plugin Enabled", None))
        self.tableWidget.horizontalHeaderItem(4).setText(QCoreApplication.translate("MainWindow", "Plugin State", None))
