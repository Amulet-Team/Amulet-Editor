from dataclasses import dataclass
import weakref
from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget

from amulet.level import Level

from amulet.app.exception import CatchExceptionDialog

from .._tab import TabAboutToHide, TabAboutToClose, ToolAboutToHide
from ._toolbar import ToolBar, ToolbarButton
from ..dock._impl import DockMainWidget


@dataclass(frozen=True)
class LayoutStorage:
    identifier: str
    button: ToolbarButton
    widget: QWidget


class LevelTabWidget(QWidget, TabAboutToClose, TabAboutToHide):
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

    def tab_about_to_hide(self) -> bool:
        widget = self._widget_stack.currentWidget()
        if isinstance(widget, ToolAboutToHide):
            return widget.tool_about_to_hide()
        return True

    def tab_about_to_close(self) -> bool:
        widget = self._widget_stack.currentWidget()
        if isinstance(widget, ToolAboutToHide):
            if not widget.tool_about_to_hide():
                return False
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
        widget: QWidget | str,
    ) -> None:
        if identifier in self._tool_id_to_storage:
            raise ValueError(f"Tool with identifier {identifier} already exists.")

        if isinstance(widget, str):
            widget = DockMainWidget(self._level, widget)

        self._widget_stack.addWidget(widget)
        button = ToolbarButton(name, icon_path)

        weak_widget_stack = weakref.ref(self._widget_stack)

        def pre_show_widget(veto: Callable[[], None]) -> None:
            widget_stack = weak_widget_stack()
            if widget_stack is None:
                return
            current_widget = widget_stack.currentWidget()
            if widget is current_widget:
                return
            if isinstance(current_widget, ToolAboutToHide):
                with CatchExceptionDialog(
                    f"Error in {current_widget}.tool_about_to_hide()"
                ):
                    if not current_widget.tool_about_to_hide():
                        veto()

        def show_widget() -> None:
            widget_stack = weak_widget_stack()
            if widget_stack is None:
                return
            current_widget = widget_stack.currentWidget()
            if widget is current_widget:
                return
            widget_stack.setCurrentWidget(widget)

        button.pre_clicked.connect(
            pre_show_widget, type=Qt.ConnectionType.DirectConnection
        )
        button.clicked.connect(show_widget)
        self._toolbar.add_layout_button(button)
        self._tool_id_to_storage[identifier] = LayoutStorage(identifier, button, widget)

    def activate_tool(self, identifier: str) -> None:
        self._tool_id_to_storage[identifier].button.click()


class LevelTabWidgetAPI:
    def __init__(self, level_tab: LevelTabWidget) -> None:
        self._level_tab = weakref.ref(level_tab)

    def add_tool(
        self,
        *,
        identifier: str,
        name: str | tuple[str, str, str | None],
        icon_path: str,
        widget: QWidget | str,
    ) -> None:
        """
        Add a new tool.
        :param identifier: A unique identifier for the tool e.g. "my_namespace.my_plugin.my_tool"
        :param name: The name to display next to the button. This can be a string or localisation tuple passed to QCoreApplication.translate.
        :param icon_path: The path to the icon to display in the button.
        :param widget:
            1) The widget that is displayed when the tool is selected.
            2) The identifier for a dock layout.
        """
        level_tab = self._level_tab()
        if level_tab is not None:
            level_tab.add_tool(identifier, name, icon_path, widget)

    def activate_tool(self, identifier: str) -> None:
        """This simulates the user clicking the button for the tool."""
        level_tab = self._level_tab()
        if level_tab is not None:
            level_tab.activate_tool(identifier)
