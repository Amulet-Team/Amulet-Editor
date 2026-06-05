import traceback
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QEvent, QCoreApplication, QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QTabBar,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from amulet.app.exception import CatchExceptionDialog, display_exception

from amulet.level.abc import Level

from ._home_tab import HomeTabWidget
from ._level_tab import LevelTabWidget, LevelTabWidgetAPI
from ._tab import WindowTabClose


@dataclass(frozen=True)
class LevelTabStorage:
    level: Level
    widget: QWidget
    api: LevelTabWidgetAPI


class EditorMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # This is here to stop the window closing and reopening when the first QOpenGLWidget is added.
        self._dummy_gl_widget = QOpenGLWidget(self)
        self._dummy_gl_widget.hide()

        self._central_widget = QWidget(self)
        self._central_layout = QVBoxLayout()
        self._central_layout.setContentsMargins(0, 0, 0, 0)
        self._central_layout.setSpacing(0)
        self._central_widget.setLayout(self._central_layout)

        self._tabs = QTabWidget()
        self._tab_bar = self._tabs.tabBar()
        self._tabs.setStyleSheet("QTabBar::tab { min-width: 100px; }")
        self._tabs.setTabsClosable(True)
        self._tabs.setTabBarAutoHide(True)
        self._central_layout.addWidget(self._tabs)

        self._home_widget = HomeTabWidget()
        self._tabs.addTab(self._home_widget, "Home")
        self._tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        self.setCentralWidget(self._central_widget)

        self._widget_to_storage: dict[QWidget, LevelTabStorage] = {}
        self._level_to_storage: dict[Level, LevelTabStorage] = {}

        self._tabs.tabCloseRequested.connect(self._tab_close_requested)

        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self._tabs.tabBar().setTabText(
            0,
            QCoreApplication.translate(
                "plugin.amulet.editor.EditorMainWindow",
                "home",
                None,
            ),
        )

    def _tab_close_requested(self, index: int) -> None:
        with CatchExceptionDialog("Error in EditorMainWindow._tab_close_requested"):
            widget = self._tabs.widget(index)
            if widget is None or widget is self._home_widget:
                return
            storage = self._widget_to_storage[widget]
            level = storage.level
            if self.request_close_level_tab(level):
                with level.lock():
                    level.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        levels = list(self._level_to_storage.keys())
        active_storage = self._widget_to_storage.get(self._tabs.currentWidget())
        if active_storage is not None:
            # Remove the active level last to minimise show/hide events
            levels.remove(active_storage.level)
            levels.append(active_storage.level)
        veto = False
        for level in levels:
            if self.request_close_level_tab(level):
                with level.lock():
                    level.close()
            else:
                veto = True
        if veto:
            event.ignore()

    def has_level_tab(self, level: Level) -> bool:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        return level in self._level_to_storage

    def get_level_tab(self, level: Level) -> LevelTabWidgetAPI:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        return self._level_to_storage[level].api

    def add_level_tab(self, level: Level, show: bool = False) -> None:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        storage = self._level_to_storage.get(level)
        if storage is None:
            try:
                widget = LevelTabWidget(level)
            except Exception as e:
                display_exception(
                    title="Failed creating level tab",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
                return
            else:
                storage = LevelTabStorage(level, widget, LevelTabWidgetAPI(widget))
                self._level_to_storage[level] = storage
                self._widget_to_storage[widget] = storage
                self._tabs.addTab(widget, level.level_name)
        if show:
            self.show_level_tab(level)

    def show_level_tab(self, level: Level) -> None:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        storage = self._level_to_storage.get(level)
        if storage is None:
            raise RuntimeError("Level tab does not exist")
        self._tabs.setCurrentWidget(storage.widget)

    def request_close_level_tab(self, level: Level) -> bool:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        storage = self._level_to_storage.get(level)
        if storage is None:
            # We are not aware of this level
            return True
        widget = storage.widget
        if isinstance(widget, WindowTabClose):
            with CatchExceptionDialog("Failed closing tab"):
                if not widget.close_tab():
                    # The tab vetoed the close
                    return False
        self._tabs.removeTab(self._tabs.indexOf(widget))
        self._level_to_storage.pop(level, None)
        self._widget_to_storage.pop(widget, None)
        return True


class AmuletEditorAPI(QObject):
    """This is the public interface to interact with the editor."""

    def __init__(self) -> None:
        super().__init__()
        self._main_window = EditorMainWindow()
        self._main_window.showMaximized()

    # This is emitted once for each level tab, just after it is first shown.
    level_tab_init = Signal(Level)

    def has_level_tab(self, level: Level) -> bool:
        """Check if a tab exists for the level."""
        return self._main_window.has_level_tab(level)

    def get_level_tab(self, level: Level) -> LevelTabWidgetAPI:
        """Get the tab for the level."""
        return self._main_window.get_level_tab(level)

    def add_level_tab(self, level: Level, show: bool = False) -> None:
        """
        Add a tab for the level.
        If a tab already exists for the level, this will do nothing.
        If show is True, the tab will be shown.
        """
        self._main_window.add_level_tab(level, show)

    def show_level_tab(self, level: Level) -> None:
        """Switch to the tab for the level."""
        self._main_window.show_level_tab(level)

    def request_close_level_tab(self, level: Level) -> bool:
        """
        Request closing the tab for the level.
        Returns True if the tab was closed.
        If the tab was closed, the level object is now your responsibility.
        """
        return self._main_window.request_close_level_tab(level)


_api: AmuletEditorAPI | None = None


def init_and_show_editor() -> None:
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    global _api
    if _api is not None:
        raise RuntimeError("Amulet Editor has already been initialised")
    _api = AmuletEditorAPI()


def get_amulet_editor() -> AmuletEditorAPI:
    """
    Get the Amulet editor API.
    The API must only be interacted with from the main thread.
    This will fail if the editor has not been initialised.
    """
    if _api is None:
        raise RuntimeError("Amulet editor has not been initialised")
    return _api
