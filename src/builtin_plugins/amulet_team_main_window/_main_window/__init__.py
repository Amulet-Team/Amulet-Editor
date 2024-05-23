from __future__ import annotations
from typing import TypeAlias
from threading import Lock

from PySide6.QtGui import QShortcut
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from amulet_team_inspector import show_inspector

from .main_window import Ui_AmuletMainWindow
from .toolbar import ButtonProxy
from .._tab_engine import RecursiveSplitter


# Terminology
# A Widget is an atomic GUI element within the program
# A Layout is an arrangement of widgets
# A tool button is a button in the toolbar. It can be configured to activate a layout or just run some code.

# A layout system.
#   controls where widgets are
#   Layout configurations are associated with identifiers
#   Layouts can be switched with code


UID: TypeAlias = str
UUID: TypeAlias = str


class AmuletMainWindow(Ui_AmuletMainWindow):
    """The main window in the Amulet application.
    It contains a toolbar and a tab widget engine.
    """

    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)

        # self._view_classes: dict[type[View], UUID] = {}
        # self._view_containers: list[ViewContainer] = [self._view_container]
        # self._active_view = self._view_container
        f12 = QShortcut(Qt.Key.Key_F12, self)
        f12.activated.connect(show_inspector)

    # def activate_view(self, view_cls: type[View]):
    #     """
    #     Enable a view registered to the given identifier.
    #     If a view of this type already exists it will be activated otherwise a new view will be created in the active container.
    #
    #     :param view_cls: The view type to enable
    #     """
    #     if view_cls not in self._view_classes:
    #         raise ValueError(f"View type {view_cls} has not been registered")
    #
    #     # Scan the view containers to see if a view of this type already exists
    #     for existing_view in self._view_containers:
    #         if existing_view.view_cls is view_cls:
    #             break
    #     else:
    #         existing_view = None
    #
    #     if existing_view is None:
    #         # Replace the active view
    #         view = view_cls()
    #         old_view = self._view_container.swap_view(view)
    #         # TODO: implement view caching
    #         if old_view is not None:
    #             old_view.deleteLater()
    #     else:
    #         existing_view.get_view().activate_view()
    #
    #     self._toolbar.activate(self._view_classes[view_cls])

    # def set_layout(self, layout: type[TabWidget] | Layout) -> None:
    #     """Configure the layout as requested"""
    #     if isinstance(layout, Layout):
    #         raise NotImplementedError
    #     elif isclass(layout) and issubclass(layout, TabWidget):
    #         if not is_registered_widget(layout):
    #             raise RuntimeError(f"Widget {layout} has not been registered.")
    #         for index in range(self.view_container.count() - 1, -1, -1):
    #             widget = self.view_container.widget(index)
    #             widget.hide()
    #             widget.deleteLater()
    #         try:
    #             widget = layout()
    #         except Exception as e:
    #             display_exception(
    #                 title=f"Error initialising Widget {layout}",
    #                 error=str(e),
    #                 traceback=traceback.format_exc(),
    #             )
    #         else:
    #             tab_widget = StackedTabWidget()
    #             tab_widget.add_page(widget)
    #             self.view_container.insertWidget(0, tab_widget)
    #     else:
    #         raise RuntimeError

    def replace_view_container(self, new_view_container: RecursiveSplitter) -> RecursiveSplitter:
        old_view_container = self.view_container
        layout_item = self._main_layout.replaceWidget(old_view_container, new_view_container, options=Qt.FindChildOption.FindDirectChildrenOnly)
        assert old_view_container is layout_item.widget()
        self.view_container = new_view_container
        return old_view_container


# The lock must be acquired before reading/writing the objects below.
_lock = Lock()
_main_window: AmuletMainWindow | None = None


def get_main_window() -> AmuletMainWindow:
    """Get the main window instance.
    This is a private function that must not be used outside of this plugin."""
    global _main_window
    with _lock:
        if _main_window is None:
            _main_window = AmuletMainWindow()
        return _main_window
