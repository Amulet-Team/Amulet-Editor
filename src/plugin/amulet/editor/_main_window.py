import traceback
from dataclasses import dataclass
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, QEvent, QCoreApplication, QThread, Qt
from PySide6.QtGui import QCloseEvent, QShortcut, QMouseEvent
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QTabBar,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from amulet.utils.event import EventToken

from amulet.level.abc import Level

from amulet.app.exception import CatchExceptionDialog, display_exception
from amulet.app.qt.signal import TypeFormSignal

from plugin.amulet.inspector.inspector import InspectorTool

from ._home_tab import HomeTabWidget
from ._level_tab import LevelTabWidget, LevelTabWidgetAPI
from ._tab import TabAboutToClose, TabAboutToHide


@dataclass(frozen=True)
class LevelTabStorage:
    level: Level
    widget: QWidget
    api: LevelTabWidgetAPI
    level_name_changed_token: EventToken[str]


class TabBar(QTabBar):
    # The tab is about to change. If the callback is called, the tab change is vetoed.
    tabAboutToChange = TypeFormSignal(Callable[[], None])

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0 and index != self.currentIndex():
                veto = False

                def set_veto() -> None:
                    nonlocal veto
                    veto = True

                self.tabAboutToChange.emit(set_veto)
                if veto:
                    return
        super().mousePressEvent(event)


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
        self._tab_bar = TabBar()
        self._tabs.setTabBar(self._tab_bar)
        self._tabs.setStyleSheet("QTabBar::tab { min-width: 100px; }")
        self._tabs.setTabsClosable(True)
        self._tabs.setTabBarAutoHide(True)
        self._central_layout.addWidget(self._tabs)

        self._home_widget = HomeTabWidget()
        self._tabs.addTab(self._home_widget, "")
        self._tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        self.setCentralWidget(self._central_widget)

        self._widget_to_storage: dict[QWidget, LevelTabStorage] = {}
        self._level_to_storage: dict[Level, LevelTabStorage] = {}

        self._tab_bar.tabAboutToChange.connect(self._tab_changing)
        self._tabs.tabCloseRequested.connect(self._tab_close_requested)

        self._inspector: InspectorTool | None = None
        self._f12_shortcut = QShortcut("F12", self)
        self._f12_shortcut.activated.connect(self._show_inspector)

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

    def _show_inspector(self) -> None:
        if self._inspector is None:
            self._inspector = InspectorTool(self)
        else:
            self._inspector.reload()
        self._inspector.show()

    def _tab_changing(self, veto: Callable[[], None]) -> None:
        widget = self._tabs.currentWidget()
        if isinstance(widget, TabAboutToHide):
            with CatchExceptionDialog(f"Error in {widget}.tab_about_to_hide()"):
                if not widget.tab_about_to_hide():
                    veto()

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

                def on_level_name_changed(level_name: str) -> None:
                    self._tabs.setTabText(self._tabs.indexOf(widget), level_name)

                storage = LevelTabStorage(
                    level,
                    widget,
                    LevelTabWidgetAPI(widget),
                    level.level_name_changed.connect(on_level_name_changed),
                )
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
        current_widget = self._tabs.currentWidget()
        if isinstance(current_widget, TabAboutToHide):
            with CatchExceptionDialog(f"Error in {current_widget}.tab_about_to_hide()"):
                if not current_widget.tab_about_to_hide():
                    return
        self._tabs.setCurrentWidget(storage.widget)

    def request_close_level_tab(self, level: Level) -> bool:
        if not QThread.isMainThread():
            raise RuntimeError("This must be called by the main thread")
        storage = self._level_to_storage.get(level)
        if storage is None:
            # We are not aware of this level
            return True
        widget = storage.widget
        if isinstance(widget, TabAboutToClose):
            with CatchExceptionDialog(f"Error in {widget}.tab_about_to_close()"):
                if not widget.tab_about_to_close():
                    # The tab vetoed the close
                    return False
        self._tabs.removeTab(self._tabs.indexOf(widget))
        self._level_to_storage.pop(level, None)
        self._widget_to_storage.pop(widget, None)
        widget.setParent(None)
        widget.deleteLater()
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
