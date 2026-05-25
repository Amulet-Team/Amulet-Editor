from PySide6.QtCore import QEvent, QCoreApplication, QThread
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QTabBar,
)

from amulet.app.exception import CatchExceptionDialog

from amulet.level.abc import Level

from ._home_tab import HomeWidget


class EditorMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._central_widget = QWidget(self)
        self._central_layout = QVBoxLayout()
        self._central_layout.setContentsMargins(0, 0, 0, 0)
        self._central_layout.setSpacing(0)
        self._central_widget.setLayout(self._central_layout)

        self._pages = QTabWidget()
        self._pages.setStyleSheet("QTabBar::tab { min-width: 100px; }")
        self._pages.setTabsClosable(True)
        self._pages.setTabBarAutoHide(True)
        self._central_layout.addWidget(self._pages)

        self._pages.addTab(HomeWidget(), "Home")
        self._pages.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        self.setCentralWidget(self._central_widget)

        self._localise()

        self._widgets: dict[Level, QWidget] = {}
        self._levels: dict[QWidget, Level] = {}

        self._pages.tabCloseRequested.connect(self._tab_close_requested)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self._pages.tabBar().setTabText(
            0,
            QCoreApplication.translate(
                "plugin.amulet.editor.EditorMainWindow",
                "home",
                None,
            ),
        )

    def _tab_close_requested(self, index: int) -> None:
        with CatchExceptionDialog("Failed closing level"):
            widget = self._pages.widget(index)
            if widget is None:
                return
            level = self._levels[widget]
            self._close_level_tab(level)
            with level.lock():
                level.close()

    def _add_level_tab(self, level: Level, show: bool = False) -> None:
        widget = self._widgets.get(level)
        if widget is None:
            widget = QWidget()
            self._widgets[level] = widget
            self._levels[widget] = level
            index = self._pages.addTab(widget, level.level_name)
            # self._pages.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        if show:
            self._pages.setCurrentWidget(widget)

    def _show_level_tab(self, level: Level) -> None:
        widget = self._widgets.get(level)
        if widget is None:
            raise RuntimeError("Level tab does not exist")
        self._pages.setCurrentWidget(widget)

    def _close_level_tab(self, level: Level) -> None:
        widget = self._widgets.pop(level, None)
        if widget is None:
            return
        self._pages.removeTab(self._pages.indexOf(widget))
        del self._levels[widget]


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


def close_level_tab(level: Level) -> None:
    """
    Closes the tab for the level.
    It is your responsibility to close the level object.
    """
    if not QThread.isMainThread():
        raise RuntimeError("This must be called by the main thread")
    if main_window is None:
        raise RuntimeError("Main window does not exist")
    main_window._close_level_tab(level)
