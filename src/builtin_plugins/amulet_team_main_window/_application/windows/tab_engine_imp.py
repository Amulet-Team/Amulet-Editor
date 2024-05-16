from typing import Union

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMouseEvent

from amulet_team_main_window._application.tab_engine import (
    AbstractTabContainer,
    AbstractTabBar,
    AbstractTabContainerWidget,
    AbstractStackedTabWidget,
    TabPage,
)
import amulet_team_main_window._application.windows.main_window as main_window
import amulet_team_main_window._application.windows.sub_window as sub_window


class TabContainerWidget(AbstractTabContainerWidget):
    def _new_stacked_tab_widget(self) -> AbstractStackedTabWidget:
        return StackedTabWidget()

    def _on_drop_in_space(
        self, dragged_widget: Union[QWidget, TabPage], drop_event: QMouseEvent
    ) -> None:
        new_window = sub_window.AmuletSubWindow(main_window.AmuletMainWindow.instance())
        tab_widget = StackedTabWidget()
        new_window.view_container.addWidget(tab_widget)
        tab_widget.add_page(dragged_widget)
        new_window.move(drop_event.globalPosition().toPoint())
        new_window.show()


class TabContainer(AbstractTabContainer):
    def _new_tab_container_widget(self) -> AbstractTabContainerWidget:
        return TabContainerWidget()


class TabBar(AbstractTabBar):
    def _new_tab_container(self) -> AbstractTabContainer:
        return TabContainer()


class StackedTabWidget(AbstractStackedTabWidget):
    def _new_tab_bar(self) -> AbstractTabBar:
        return TabBar()

    def _on_last_removed(self) -> None:
        parent = self.window()
        if isinstance(parent, main_window.AmuletMainWindow):
            # If this widget is the last AbstractStackedTabWidget in the AmuletMainWindow and has no tabs, open the default tab
            # TODO: add the default page
            print("add page")
        elif isinstance(parent, sub_window.AmuletSubWindow):
            parent.deleteLater()
        else:
            raise RuntimeError
