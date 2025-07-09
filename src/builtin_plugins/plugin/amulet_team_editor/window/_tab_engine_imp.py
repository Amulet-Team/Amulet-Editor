from PySide6.QtGui import QMouseEvent

from ._tab_engine import (
    AbstractTabContainer,
    AbstractTabBar,
    AbstractTabContainerWidget,
    AbstractStackedTabWidget,
    TabWidget,
)
from plugin.amulet_team_editor.window import (
    _main as _main_window,
    _child as _child_window,
)


class TabContainerWidget(AbstractTabContainerWidget):
    def _new_stacked_tab_widget(self) -> AbstractStackedTabWidget:
        return StackedTabWidget()

    def _on_drop_in_space(
        self, dragged_widget: TabWidget, drop_event: QMouseEvent
    ) -> None:
        new_window = _child_window.create_sub_window()
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
        if isinstance(parent, _main_window.AmuletMainWindow):
            # If this widget is the last AbstractStackedTabWidget in the AmuletMainWindow and has no tabs, open the default tab
            # TODO: add the default page
            print("add page")
        elif isinstance(parent, _child_window.AmuletChildWindow):
            parent.deleteLater()
        else:
            raise RuntimeError
