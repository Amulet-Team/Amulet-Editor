from functools import partial
from typing import Optional

from amulet_editor.application import appearance
from amulet_editor.application.appearance import Theme
from amulet_editor.data import packages, project
from amulet_editor.models.package import AmuletTool
from amulet_editor.models.widgets import ADragContainer, ATooltipIconButton
from amulet_editor.tools.packages import Packages
from amulet_editor.tools.settings import Settings
from amulet_editor.tools.startup import Startup
from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt
from PySide6.QtGui import QAction, QKeyEvent, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

MINIMUM_PANEL_WIDTH = 250
DEFAULT_PANEL_WIDTH = 300


class AmuletWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setupUi()

        # Setup side menu
        self.btng_menus = QButtonGroup(self)
        self.active_tool = Startup()
        self.secondary_panel_none = QWidget()

        self.load_tool(self.active_tool)
        self.load_tool(Packages(), True)
        self.load_tool(Settings(), True)

        self.btng_menus.buttons()[0].setChecked(True)
        self.show_tool(self.active_tool)

        # Connect signals
        self.spl_horizontal.splitterMoved.connect(self.update_panel_sizes)

        # Connect restyle signal and apply current theme
        appearance.changed.connect(self.theme_changed)
        project.changed.connect(self.reload_project)

        # Connect menu options
        self.act_show_primary_panel.setCheckable(True)
        self.act_show_primary_panel.setChecked(True)
        self.act_show_primary_panel.triggered.connect(self.toggle_primary_panel)
        self.act_show_secondary_panel.setCheckable(True)
        self.act_show_secondary_panel.setChecked(False)
        self.act_show_secondary_panel.triggered.connect(self.toggle_secondary_panel)
        self.act_close_project.triggered.connect(self.close_project)

        for theme_name in appearance.list_themes():
            action = QAction(self.mn_appearance)

            action.setCheckable(True)
            if theme_name == appearance.theme().name:
                action.setChecked(True)
            action.setText(theme_name)

            action.triggered.connect(partial(appearance.set_theme, theme_name))

            self.mn_appearance.addAction(action)

    def close_project(self) -> None:
        self.unload_tools()

        startup_tool = Startup()
        self.load_tool(startup_tool)
        self.show_tool(startup_tool)

        self.act_close_project.setEnabled(False)

    def reload_project(self, project_root: str) -> None:
        """
        Unload all tools currently in use and replace them with new instances.
        """
        self.unload_tools()

        tools = packages.list_tools()
        for tool in tools:
            self.load_tool(tool)

        self.show_tool(tools[0])

        self.act_close_project.setEnabled(True)

    def update_panel_sizes(self, distance: int, index: int) -> None:
        """
        Detect whether both panels can fit on screen and determine which panel should be collapsed if there is only space for one.
        """
        page_width = self.spl_horizontal.width()

        if not self.swgt_primary_panel.visibleRegion().isEmpty():
            page_width = page_width - self.swgt_primary_panel.width()

        if not self.swgt_secondary_panel.visibleRegion().isEmpty():
            page_width = page_width - self.swgt_secondary_panel.width()

        if page_width < self.swgt_pages.minimumWidth():
            if index == 1:
                self.act_show_secondary_panel.setChecked(False)
                self.toggle_secondary_panel()
            elif index == 2:
                self.act_show_primary_panel.setChecked(False)
                self.toggle_primary_panel()

    def toggle_primary_panel(self) -> None:
        """
        Detect primary panel view state and toggle panel to match menu option.
        """
        if (
            self.act_show_primary_panel.isChecked()
            and self.swgt_primary_panel.visibleRegion().isEmpty()
        ):
            if not self.swgt_secondary_panel.visibleRegion().isEmpty():
                secondary_panel_width = self.swgt_secondary_panel.width()
                page_width = (
                    self.spl_horizontal.width()
                    - secondary_panel_width
                    - DEFAULT_PANEL_WIDTH
                )
                if page_width < self.swgt_pages.minimumWidth():
                    secondary_panel_width = 0
                    page_width = self.spl_horizontal.width() - DEFAULT_PANEL_WIDTH
                    self.act_show_secondary_panel.setChecked(False)
            else:
                secondary_panel_width = 0
                page_width = self.spl_horizontal.width() - DEFAULT_PANEL_WIDTH

            self.spl_horizontal.setSizes(
                [DEFAULT_PANEL_WIDTH, page_width, secondary_panel_width]
            )
        elif not self.swgt_primary_panel.visibleRegion().isEmpty():
            secondary_panel_width = (
                self.swgt_secondary_panel.width()
                if self.act_show_secondary_panel.isChecked()
                else 0
            )
            page_width = self.spl_horizontal.width() - secondary_panel_width
            self.spl_horizontal.setSizes([0, page_width, secondary_panel_width])

    def toggle_secondary_panel(self) -> None:
        """
        Detect secondary panel view state and toggle panel to match menu option.
        """
        if (
            self.act_show_secondary_panel.isChecked()
            and self.swgt_secondary_panel.visibleRegion().isEmpty()
        ):
            if not self.swgt_primary_panel.visibleRegion().isEmpty():
                primary_panel_width = self.swgt_primary_panel.width()
                page_width = (
                    self.spl_horizontal.width()
                    - primary_panel_width
                    - DEFAULT_PANEL_WIDTH
                )
                if page_width < self.swgt_pages.minimumWidth():
                    primary_panel_width = 0
                    page_width = self.spl_horizontal.width() - DEFAULT_PANEL_WIDTH
                    self.act_show_primary_panel.setChecked(False)
            else:
                primary_panel_width = 0
                page_width = self.spl_horizontal.width() - DEFAULT_PANEL_WIDTH

            self.spl_horizontal.setSizes(
                [primary_panel_width, page_width, DEFAULT_PANEL_WIDTH]
            )
        elif not self.swgt_secondary_panel.visibleRegion().isEmpty():
            primary_panel_width = (
                self.swgt_primary_panel.width()
                if self.act_show_primary_panel.isChecked()
                else 0
            )
            page_width = self.spl_horizontal.width() - primary_panel_width
            self.spl_horizontal.setSizes([primary_panel_width, page_width, 0])

    def load_tool(self, tool: AmuletTool, static: bool = False) -> None:
        """
        Loads tool into the main application toolbar.
        Tools marked as static are considered core to the functionality of the editor and thus cannot be removed once loaded.
        """
        icon_button = ATooltipIconButton(tool.icon_name, self)
        icon_button.clicked.connect(partial(self.show_tool, tool))
        icon_button.setCheckable(True)
        icon_button.setFixedSize(QSize(40, 40))
        icon_button.setToolTip(tool.name)
        icon_button.setIconSize(QSize(30, 30))

        self.btng_menus.addButton(icon_button)

        if static:
            self.lyt_static_tools.addWidget(icon_button)
        else:
            self.wgt_dynamic_tools.add_item(icon_button)

        tool.page.changed.connect(partial(self.change_page, tool))
        tool.primary_panel.changed.connect(partial(self.change_primary_panel, tool))
        tool.secondary_panel.changed.connect(partial(self.change_secondary_panel, tool))

    def unload_tools(self) -> None:
        # TODO: This should also clear corresponding panels and pages
        for index in reversed(range(self.wgt_dynamic_tools.layout().count())):
            self.wgt_dynamic_tools.layout().itemAt(index).widget().deleteLater()

    def show_tool(self, tool: AmuletTool) -> None:
        self.active_tool = tool
        self.lbl_primary_panel_title.setText(tool.name)
        self.show_page(tool.page.widget())
        self.show_primary_panel(tool.primary_panel.widget())
        self.show_secondary_panel(tool.secondary_panel.widget())

    def show_page(self, page: QWidget) -> None:
        if page not in self.swgt_pages.children():
            self.swgt_pages.addWidget(page)
        self.swgt_pages.setCurrentWidget(page)

    def show_primary_panel(self, panel: QWidget) -> None:
        if panel not in self.swgt_primary_panel.children():
            self.swgt_primary_panel.addWidget(panel)
        self.swgt_primary_panel.setCurrentWidget(panel)

    def show_secondary_panel(self, panel: Optional[QWidget]) -> None:
        if panel is None:
            panel = self.secondary_panel_none
        if panel not in self.swgt_secondary_panel.children():
            self.swgt_secondary_panel.addWidget(panel)
        self.swgt_secondary_panel.setCurrentWidget(panel)

        if (
            panel is not self.secondary_panel_none
            and self.swgt_secondary_panel.visibleRegion().isEmpty()
        ):
            self.act_show_secondary_panel.setChecked(True)
            self.toggle_secondary_panel()

    def change_page(self, tool: AmuletTool, widget: QWidget) -> None:
        if self.active_tool == tool:
            self.show_page(widget)

    def change_primary_panel(self, tool: AmuletTool, widget: QWidget) -> None:
        if self.active_tool == tool:
            self.show_primary_panel(widget)

    def change_secondary_panel(
        self, tool: AmuletTool, widget: Optional[QWidget]
    ) -> None:
        if self.active_tool == tool:
            self.show_secondary_panel(widget)

    def theme_changed(self, theme: Theme) -> None:
        for theme_action in self.mn_appearance.actions():
            if theme_action.text() == theme.name:
                theme_action.setChecked(True)
            else:
                theme_action.setChecked(False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update_panel_sizes(MINIMUM_PANEL_WIDTH, 1)

        return super().resizeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        focused = QApplication.focusWidget()
        if event.key() == Qt.Key_Escape and focused is not None:
            focused.clearFocus()

        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        focused = QApplication.focusWidget()
        if not focused is None:
            focused.clearFocus()

        return super().mousePressEvent(event)

    def setupUi(self):
        # Create 'Application' widget
        self.wgt_application = QWidget(self)

        # Create 'Application' layout
        self.lyt_application = QGridLayout(self.wgt_application)

        # Configure frame for 'Static Menu' items
        self.frm_static_tools = QFrame(self.wgt_application)
        self.frm_static_tools.setFixedWidth(40)

        # Configure widget for 'Dynamic Menu' items
        self.wgt_dynamic_tools = ADragContainer(self.frm_static_tools)
        self.wgt_dynamic_tools.layout().setAlignment(Qt.AlignTop)
        self.wgt_dynamic_tools.layout().setContentsMargins(0, 0, 0, 0)
        self.wgt_dynamic_tools.layout().setSpacing(0)

        # Configure 'Static Menu' layout
        self.lyt_static_tools = QVBoxLayout(self.frm_static_tools)
        self.lyt_static_tools.setSpacing(0)
        self.lyt_static_tools.setContentsMargins(0, 0, 0, 0)
        self.lyt_static_tools.addWidget(self.wgt_dynamic_tools)

        # Create splitter for 'Application' page and panels
        self.spl_horizontal = QSplitter(self.wgt_application)

        # Configure 'Primary Panel' frame
        self.frm_primary_panel = QFrame(self.spl_horizontal)
        self.frm_primary_panel.setFrameShape(QFrame.NoFrame)
        self.frm_primary_panel.setFrameShadow(QFrame.Raised)

        # Create 'Primary Panel' layout
        self.lyt_primary_panel = QVBoxLayout(self.frm_primary_panel)

        # Configure 'Primary Panel' header
        self.frm_primary_panel_header = QFrame(self.frm_primary_panel)
        self.frm_primary_panel_header.setMinimumSize(QSize(0, 25))
        self.frm_primary_panel_header.setFrameShape(QFrame.NoFrame)
        self.frm_primary_panel_header.setFrameShadow(QFrame.Raised)

        # Create title for 'Primary Panel'
        self.lbl_primary_panel_title = QLabel(self.frm_primary_panel_header)

        # Configure 'Primary Panel' header layout
        self.lyt_primary_panel_header = QHBoxLayout(self.frm_primary_panel_header)
        self.lyt_primary_panel_header.addWidget(self.lbl_primary_panel_title)
        self.lyt_primary_panel_header.setSpacing(0)
        self.lyt_primary_panel_header.setContentsMargins(9, 0, 9, 0)

        # Configure 'Primary Panel' stacked widget (container for 'Primary Panel' widgets)
        self.swgt_primary_panel = QStackedWidget(self.frm_primary_panel)
        spol_pkg_primary_panel = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        spol_pkg_primary_panel.setHorizontalStretch(0)
        spol_pkg_primary_panel.setVerticalStretch(0)
        self.swgt_primary_panel.setSizePolicy(spol_pkg_primary_panel)
        self.swgt_primary_panel.setMinimumSize(QSize(MINIMUM_PANEL_WIDTH, 0))

        # Configure 'Primary Panel' layout
        self.lyt_primary_panel.addWidget(self.frm_primary_panel_header)
        self.lyt_primary_panel.addWidget(self.swgt_primary_panel)
        self.lyt_primary_panel.setSpacing(0)
        self.lyt_primary_panel.setContentsMargins(0, 0, 0, 0)

        # Configure 'Secondary Panel' frame
        self.frm_secondary_panel = QFrame(self.spl_horizontal)
        self.frm_secondary_panel.setFrameShape(QFrame.NoFrame)
        self.frm_secondary_panel.setFrameShadow(QFrame.Raised)

        # Create 'Secondary Panel' layout
        self.lyt_secondary_panel = QVBoxLayout(self.frm_secondary_panel)

        # Configure 'Secondary Panel' header
        self.frm_secondary_panel_header = QFrame(self.frm_secondary_panel)
        self.frm_secondary_panel_header.setMinimumSize(QSize(0, 25))
        self.frm_secondary_panel_header.setFrameShape(QFrame.NoFrame)
        self.frm_secondary_panel_header.setFrameShadow(QFrame.Raised)

        # Create title for 'Secondary Panel'
        self.lbl_secondary_panel_title = QLabel(self.frm_secondary_panel_header)

        # Configure 'Secondary Panel' header layout
        self.lyt_secondary_panel_header = QHBoxLayout(self.frm_secondary_panel_header)
        self.lyt_secondary_panel_header.addWidget(self.lbl_secondary_panel_title)
        self.lyt_secondary_panel_header.setSpacing(0)
        self.lyt_secondary_panel_header.setContentsMargins(9, 0, 9, 0)

        # Configure 'Secondary Panel' stacked widget (container for 'Secondary Panel' widgets)
        self.swgt_secondary_panel = QStackedWidget(self.frm_secondary_panel)
        spol_pkg_secondary_panel = QSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Preferred
        )
        spol_pkg_secondary_panel.setHorizontalStretch(0)
        spol_pkg_secondary_panel.setVerticalStretch(0)
        self.swgt_secondary_panel.setSizePolicy(spol_pkg_secondary_panel)
        self.swgt_secondary_panel.setMinimumSize(QSize(MINIMUM_PANEL_WIDTH, 0))

        # Configure 'Secondary Panel' layout
        self.lyt_secondary_panel.addWidget(self.frm_secondary_panel_header)
        self.lyt_secondary_panel.addWidget(self.swgt_secondary_panel)
        self.lyt_secondary_panel.setSpacing(0)
        self.lyt_secondary_panel.setContentsMargins(0, 0, 0, 0)

        # Configure 'Pages' stacked widget (container for 'Page' widgets)
        self.swgt_pages = QStackedWidget(self.spl_horizontal)
        spol_pages = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        spol_pages.setHorizontalStretch(1)
        spol_pages.setVerticalStretch(0)
        self.swgt_pages.setSizePolicy(spol_pages)
        self.swgt_pages.setMinimumSize(QSize(300, 200))

        # Configure splitter for 'Application' page and panels
        self.spl_horizontal.addWidget(self.frm_primary_panel)
        self.spl_horizontal.addWidget(self.swgt_pages)
        self.spl_horizontal.addWidget(self.frm_secondary_panel)
        self.spl_horizontal.setOrientation(Qt.Horizontal)
        self.spl_horizontal.setHandleWidth(0)

        # Configure 'Application' layout
        self.lyt_application.addWidget(self.frm_static_tools, 0, 0, 1, 1)
        self.lyt_application.addWidget(self.spl_horizontal, 0, 1, 1, 1)
        self.lyt_application.setSpacing(0)
        self.lyt_application.setContentsMargins(0, 0, 0, 0)

        # Create 'Menu Bar'
        self.mnb_amulet = QMenuBar(self)
        self.mnb_amulet.setGeometry(QRect(0, 0, 720, 25))
        self.mnb_amulet.setMinimumSize(QSize(0, 25))

        # Create menus
        self.mn_file = QMenu(self.mnb_amulet)
        self.mn_preferences = QMenu(self.mn_file)
        self.mn_open_recent = QMenu(self.mn_file)
        self.mn_edit = QMenu(self.mnb_amulet)
        self.mn_view = QMenu(self.mnb_amulet)
        self.mn_appearance = QMenu(self.mn_view)
        self.mn_editor = QMenu(self.mn_view)

        # Configure 'Open Recent' menu
        self.act_none = QAction(self.mn_open_recent)
        self.act_clear_recently_opened = QAction(self.mn_open_recent)
        self.act_none.setEnabled(False)

        self.mn_open_recent.addAction(self.act_none)
        self.mn_open_recent.addSeparator()
        self.mn_open_recent.addAction(self.act_clear_recently_opened)

        # Configure 'Preferences' menu
        self.act_settings = QAction(self.mn_preferences)
        self.act_keyboard_shortcuts = QAction(self.mn_preferences)

        self.mn_preferences.addAction(self.act_settings)
        self.mn_preferences.addAction(self.act_keyboard_shortcuts)

        # Configure 'File' menu
        self.act_new_window = QAction(self.mn_file)
        self.act_open_project = QAction(self.mn_file)
        self.act_save = QAction(self.mn_file)
        self.act_save_as = QAction(self.mn_file)
        self.act_save_all = QAction(self.mn_file)
        self.act_close_project = QAction(self.mn_file)
        self.act_close_project.setEnabled(False)

        self.mn_file.addAction(self.act_new_window)
        self.mn_file.addSeparator()
        self.mn_file.addAction(self.act_open_project)
        self.mn_file.addAction(self.mn_open_recent.menuAction())
        self.mn_file.addSeparator()
        self.mn_file.addAction(self.act_save)
        self.mn_file.addAction(self.act_save_as)
        self.mn_file.addAction(self.act_save_all)
        self.mn_file.addSeparator()
        self.mn_file.addAction(self.mn_preferences.menuAction())
        self.mn_file.addSeparator()
        self.mn_file.addAction(self.act_close_project)

        # Configure 'Edit' menu
        self.act_undo = QAction(self.mn_edit)
        self.act_redo = QAction(self.mn_edit)
        self.act_cut = QAction(self.mn_edit)
        self.act_copy = QAction(self.mn_edit)
        self.act_paste = QAction(self.mn_edit)
        self.act_new_project = QAction(self.mn_edit)

        self.mn_edit.addAction(self.act_undo)
        self.mn_edit.addAction(self.act_redo)
        self.mn_edit.addSeparator()
        self.mn_edit.addAction(self.act_cut)
        self.mn_edit.addAction(self.act_copy)
        self.mn_edit.addAction(self.act_paste)

        # Configure 'View' menu
        self.act_show_primary_panel = QAction(self.mn_editor)
        self.act_show_secondary_panel = QAction(self.mn_editor)

        self.mn_view.addAction(self.mn_appearance.menuAction())
        self.mn_view.addAction(self.mn_editor.menuAction())
        self.mn_editor.addAction(self.act_show_primary_panel)
        self.mn_editor.addAction(self.act_show_secondary_panel)

        # Configure 'Menu Bar'
        self.mnb_amulet.addAction(self.mn_file.menuAction())
        self.mnb_amulet.addAction(self.mn_edit.menuAction())
        self.mnb_amulet.addAction(self.mn_view.menuAction())

        self.spl_horizontal.setCollapsible(1, False)
        self.spl_horizontal.setSizes([DEFAULT_PANEL_WIDTH])

        # Create 'Status Bar'
        self.sbar_amulet_status = QStatusBar(self)

        # Configure style properties
        self.frm_static_tools.setProperty("border", "none")
        self.frm_static_tools.setProperty("backgroundColor", "surface")

        self.frm_primary_panel_header.setProperty("backgroundColor", "primary")
        self.frm_primary_panel_header.setProperty("borderBottom", "surface")
        self.frm_primary_panel_header.setProperty("color", "on_surface")

        self.frm_primary_panel.setProperty("backgroundColor", "primary")
        self.frm_primary_panel.setProperty("borderRight", "surface")
        self.frm_primary_panel.setProperty("color", "on_primary")

        self.frm_secondary_panel_header.setProperty("backgroundColor", "primary")
        self.frm_secondary_panel_header.setProperty("borderBottom", "surface")
        self.frm_secondary_panel_header.setProperty("color", "on_surface")

        self.frm_secondary_panel.setProperty("backgroundColor", "primary")
        self.frm_secondary_panel.setProperty("borderLeft", "surface")
        self.frm_secondary_panel.setProperty("color", "on_primary")

        # Configure 'Application' window
        self.resize(720, 480)
        self.setCentralWidget(self.wgt_application)
        self.setMenuBar(self.mnb_amulet)
        self.setMinimumSize(QSize(720, 480))
        self.setObjectName("AmuletWindow")
        self.setStatusBar(self.sbar_amulet_status)

        # Translate widget text
        self.retranslateUi()

    def retranslateUi(self):
        # Disable formatting to condense tranlate functions
        # fmt: off
        self.setWindowTitle(QCoreApplication.translate("AmuletWindow", "Amulet Editor", None))
        self.act_open_project.setText(QCoreApplication.translate("AmuletWindow", "Open Project...", None))
        self.act_open_project.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+O", None))
        self.act_save.setText(QCoreApplication.translate("AmuletWindow", "Save", None))
        self.act_save.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+S", None))
        self.act_save_as.setText(QCoreApplication.translate("AmuletWindow", "Save As...", None))
        self.act_save_as.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+Shift+S", None))
        self.act_save_all.setText(QCoreApplication.translate("AmuletWindow", "Save All", None))
        self.act_settings.setText(QCoreApplication.translate("AmuletWindow", "Settings", None))
        self.act_settings.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+,", None))
        self.act_keyboard_shortcuts.setText(QCoreApplication.translate("AmuletWindow", "Keyboard Shortcuts", None))
        self.act_keyboard_shortcuts.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+K, Ctrl+S", None))
        self.act_close_project.setText(QCoreApplication.translate("AmuletWindow", "Close Project", None))
        self.act_undo.setText(QCoreApplication.translate("AmuletWindow", "Undo", None))
        self.act_undo.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+Z", None))
        self.act_redo.setText(QCoreApplication.translate("AmuletWindow", "Redo", None))
        self.act_redo.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+Y", None))
        self.act_cut.setText(QCoreApplication.translate("AmuletWindow", "Cut", None))
        self.act_cut.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+X", None))
        self.act_copy.setText(QCoreApplication.translate("AmuletWindow", "Copy", None))
        self.act_copy.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+C", None))
        self.act_paste.setText(QCoreApplication.translate("AmuletWindow", "Paste", None))
        self.act_paste.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+V", None))
        self.act_none.setText(QCoreApplication.translate("AmuletWindow", "None", None))
        self.act_clear_recently_opened.setText(QCoreApplication.translate("AmuletWindow", "Clear Recently Opened", None))
        self.act_new_window.setText(QCoreApplication.translate("AmuletWindow", "New Window", None))
        self.act_new_window.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+Shift+N", None))
        self.act_new_project.setText(QCoreApplication.translate("AmuletWindow", "New Project...", None))
        self.act_new_project.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+N", None))
        self.mn_file.setTitle(QCoreApplication.translate("AmuletWindow", "File", None))
        self.mn_preferences.setTitle(QCoreApplication.translate("AmuletWindow", "Preferences", None))
        self.mn_open_recent.setTitle(QCoreApplication.translate("AmuletWindow", "Open Recent", None))
        self.mn_edit.setTitle(QCoreApplication.translate("AmuletWindow", "Edit", None))
        self.mn_view.setTitle(QCoreApplication.translate("AmuletWindow", "View", None))
        self.mn_appearance.setTitle(QCoreApplication.translate("AmuletWindow", "Appearance", None))
        self.mn_editor.setTitle(QCoreApplication.translate("AmuletWindow", "Editor", None))
        self.act_show_primary_panel.setText(QCoreApplication.translate("AmuletWindow", "Show Primary Panel", None))
        self.act_show_primary_panel.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+B", None))
        self.act_show_secondary_panel.setText(QCoreApplication.translate("AmuletWindow", "Show Secondary Panel", None))
        self.act_show_secondary_panel.setShortcut(QCoreApplication.translate("AmuletWindow", "Ctrl+Shift+B", None))
        self.lbl_primary_panel_title.setText(QCoreApplication.translate("AmuletWindow", "App Name", None))
        # fmt: on
