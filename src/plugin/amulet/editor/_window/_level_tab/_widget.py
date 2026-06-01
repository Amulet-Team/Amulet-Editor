from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget

from amulet.level import Level

from .._tab import WindowTabClose
from ._toolbar import ToolBar, ToolbarButton


@dataclass(frozen=True)
class LayoutStorage:
    identifier: str
    button: ToolbarButton
    widget: QWidget


class LevelTabWidget(QWidget, WindowTabClose):
    def __init__(self, level: Level) -> None:
        super().__init__()
        self._level = level

        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._toolbar = ToolBar(Qt.Orientation.Vertical)
        self._main_layout.addWidget(self._toolbar)

        self._widget_stack = QStackedWidget()
        self._main_layout.addWidget(self._widget_stack, 1)

        self._tool_id_to_storage: dict[str, LayoutStorage] = {}

        self._initialised = False

    def close_tab(self) -> bool:
        # TODO: If the level has unsaved changes, ask the user if they want to save them.
        return True

    def showEvent(self, event: QShowEvent, /) -> None:
        if not self._initialised:
            from .._main_window import get_amulet_editor

            self._initialised = True
            get_amulet_editor().level_tab_init.emit(self._level)

    def add_tool(
        self,
        identifier: str,
        name: str | tuple[str, str, str | None],
        icon_path: str,
        widget: QWidget,
    ) -> None:
        if identifier in self._tool_id_to_storage:
            raise ValueError(f"Tool with identifier {identifier} already exists.")

        self._widget_stack.addWidget(widget)
        button = ToolbarButton(name, icon_path)

        def show_widget() -> None:
            self._widget_stack.setCurrentWidget(widget)

        button.clicked.connect(show_widget)
        self._toolbar.add_layout_button(button)
        self._tool_id_to_storage[identifier] = LayoutStorage(identifier, button, widget)

    def activate_tool(self, identifier: str) -> None:
        self._tool_id_to_storage[identifier].button.click()


class LevelTabWidgetAPI:
    def __init__(self, level_tab: LevelTabWidget) -> None:
        self._level_tab = level_tab

    def add_tool(
        self,
        *,
        identifier: str,
        name: str | tuple[str, str, str | None],
        icon_path: str,
        widget: QWidget,
    ) -> None:
        """
        Add a new tool.
        :param identifier: A unique identifier for the tool e.g. "my_namespace.my_plugin.my_tool"
        :param name: The name to display next to the button. This can be a string or localisation tuple passed to QCoreApplication.translate.
        :param icon_path: The path to the icon to display in the button.
        :param widget: The widget that is displayed when the tool is selected.
        """
        self._level_tab.add_tool(identifier, name, icon_path, widget)

    def activate_tool(self, identifier: str) -> None:
        """This simulates the user clicking the button for the tool."""
        self._level_tab.activate_tool(identifier)
