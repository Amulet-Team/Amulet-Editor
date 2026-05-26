import traceback

from PySide6.QtCore import QEvent, QCoreApplication, QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QTabBar,
)

from amulet.app.exception import CatchExceptionDialog, display_exception

from amulet.level.abc import Level

from ._home_tab import HomeWidget
from ._level_tab import LevelWidget
from ._tab import WindowTabClose


class EditorMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

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

        self._home_widget = HomeWidget()
        self._tabs.addTab(self._home_widget, "Home")
        self._tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        self.setCentralWidget(self._central_widget)

        self._widgets: dict[Level, QWidget] = {}
        self._levels: dict[QWidget, Level] = {}

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
            level = self._levels[widget]
            if self._request_close_level_tab(level):
                with level.lock():
                    level.close()

    def _request_close_level_tab(self, level: Level) -> bool:
        widget = self._widgets.get(level)
        if widget is None:
            # We are not aware of this level
            return True
        if isinstance(widget, WindowTabClose):
            with CatchExceptionDialog("Failed closing tab"):
                if not widget.close_tab():
                    # The tab vetoed the close
                    return False
        self._tabs.removeTab(self._tabs.indexOf(widget))
        self._widgets.pop(level, None)
        self._levels.pop(widget, None)
        return True

    def _add_level_tab(self, level: Level, show: bool = False) -> None:
        widget = self._widgets.get(level)
        if widget is None:
            try:
                widget = LevelWidget(level)
            except Exception as e:
                display_exception(
                    title="Failed creating level tab",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
                return
            else:
                self._widgets[level] = widget
                self._levels[widget] = level
                self._tabs.addTab(widget, level.level_name)
        if show:
            self._show_level_tab(level)

    def _show_level_tab(self, level: Level) -> None:
        new_widget = self._widgets.get(level)
        if new_widget is None:
            raise RuntimeError("Level tab does not exist")
        self._tabs.setCurrentWidget(new_widget)

    def closeEvent(self, event: QCloseEvent) -> None:
        levels = list(self._widgets.keys())
        active_level = self._levels.get(self._tabs.currentWidget())
        if active_level is not None:
            # Remove the active level last to minimise show/hide events
            levels.remove(active_level)
            levels.append(active_level)
        veto = False
        for level in levels:
            if self._request_close_level_tab(level):
                with level.lock():
                    level.close()
            else:
                veto = True
        if veto:
            event.ignore()


main_window: EditorMainWindow | None = None


def show_main_window() -> None:
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    global main_window
    if main_window is not None:
        raise RuntimeError("Main window already exists")
    main_window = EditorMainWindow()
    main_window.showMaximized()


def add_level_tab(level: Level, show: bool = False) -> None:
    """
    Add the level to a tab in the main window.
    If a tab already exists for the level, this will do nothing.
    """
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    if main_window is None:
        raise RuntimeError("Main window does not exist")
    main_window._add_level_tab(level, show)


def show_level_tab(level: Level) -> None:
    """
    Switch to the tab for the level.
    """
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    if main_window is None:
        raise RuntimeError("Main window does not exist")
    main_window._show_level_tab(level)


def request_close_level_tab(level: Level) -> bool:
    """
    Request closing the tab for the level.
    Returns True if the tab was closed.
    If the tab was closed, the level object is now your responsibility.
    """
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    if main_window is None:
        raise RuntimeError("Main window does not exist")
    return main_window._request_close_level_tab(level)
