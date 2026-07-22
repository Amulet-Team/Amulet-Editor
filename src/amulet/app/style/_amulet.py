import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QProxyStyle,
    QApplication,
)

import amulet.app.style
from amulet.app.invoke import enqueue

Colours = [
    # light
    {
        "button_highlight": "#fdfdfd",
        "button_border": "#ababab",
        "button_light": "#fdfdfd",
        "button_dark": "#efefef",
        "button_hover_light": "#dadada",
        "button_hover_dark": "#c7c7c7",
        "button_disabled_light": "#f6f6f6",
        "button_disabled_dark": "#c7c7c7",
        "button_hover_2": "#a0a0a0",
        "button_checked_light": "#82d4ff",
        "button_checked_dark": "#82d4ff",
        "button_checked_hover_light": "#64bbe9",
        "button_checked_hover_dark": "#41ade4",
        "button_checked_disabled_light": "#4c97be",
        "button_checked_disabled_dark": "#28739a",
        "tab_widget_light": "#fcfcfc",
        "tab_widget_dark": "#fcfcfc",
    },
    # dark
    {
        "button_highlight": "#6a6a6a",
        "button_border": "#151515",
        "button_light": "#545454",
        "button_dark": "#474747",
        "button_hover_light": "#848484",
        "button_hover_dark": "#717171",
        "button_disabled_light": "#4d4d4d",
        "button_disabled_dark": "#383838",
        "button_hover_2": "#a0a0a0",
        "button_checked_light": "#4cc2ff",
        "button_checked_dark": "#3a9ccf",
        "button_checked_hover_light": "#23a0e1",
        "button_checked_hover_dark": "#2e7ca5",
        "button_checked_disabled_light": "#4c97be",
        "button_checked_disabled_dark": "#28739a",
        "tab_widget_light": "#303030",
        "tab_widget_dark": "#303030",
    },
]


def get_style_sheet(dark: bool) -> str:
    style = "dark" if dark else "light"
    down_icon_path = os.path.realpath(
        os.path.join(amulet.app.style.__path__[0], "icon", f"caret-down-{style}.svg")
    ).replace(os.sep, "/")
    close_icon_path = os.path.realpath(
        os.path.join(amulet.app.style.__path__[0], "icon", f"x.svg")
    ).replace(os.sep, "/")

    return """\
QPushButton {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_highlight},
        stop: 0.1 {button_light},
        stop: 0.9 {button_dark},
        stop: 1 {button_highlight}
    );

    border-color: {button_border};
    border-style: solid;
    border-width: 1px;
    border-radius: 3px;
    
    height: 22px;
    padding-left: 8px;
    padding-right: 8px;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_hover_light},
        stop: 1 {button_hover_dark}
    );
}}

QPushButton:disabled {{
    background: qlineargradient(
        coordinatemode: logical,
        spread: repeat,
        x1: 0, y1: 0,
        x2: 4, y2: 4,
        stop: 0 {button_disabled_light},
        stop: 0.5 {button_disabled_light},
        stop: 0.501 {button_disabled_dark},
        stop: 1 {button_disabled_dark}
    );
    color: black;
}}

QPushButton:checked {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_checked_light},
        stop: 1 {button_checked_dark}
    );
    color: black;
}}

QPushButton:checked:hover {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_checked_hover_light},
        stop: 1 {button_checked_hover_dark}
    );
    color: black;
}}

QPushButton:checked:disabled {{
    background: qlineargradient(
        coordinatemode: logical,
        spread: repeat,
        x1: 0, y1: 0,
        x2: 4, y2: 4,
        stop: 0 {button_checked_disabled_light},
        stop: 0.5 {button_checked_disabled_light},
        stop: 0.501 {button_checked_disabled_dark},
        stop: 1 {button_checked_disabled_dark}
    );
    color: black;
}}

QComboBox {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_highlight},
        stop: 0.1 {button_light},
        stop: 0.9 {button_dark},
        stop: 1 {button_highlight}
    );

    border-color: {button_border};
    border-style: solid;
    border-width: 1px;
    border-radius: 3px;
    
    height: 22px;
    padding-left: 8px;
    padding-right: 8px;
}}

QComboBox:hover {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_hover_light},
        stop: 1 {button_hover_dark}
    );
}}

QComboBox::drop-down {{
    border: 0px;
}}

QComboBox::down-arrow {{
    image: url({down_icon_path});
    width: 12px;
    height: 12px;
    padding-right: 5px;
}}


QTabWidget::pane {{
    background: {tab_widget_dark};
    
    border: none;
    
    top: -1px;
}}

QTabBar::tab {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_highlight},
        stop: 0.2 {tab_widget_light},
        stop: 1 {tab_widget_dark}
    );
    
    border-color: {button_border};
    border-style: solid;
    border-width: 1px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-width: 2px;
    
    height: 25px;
    padding-left: 5px;
    padding-right: 5px;
}}

QTabBar::tab:hover {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_hover_light},
        stop: 1 {button_hover_dark}
    );
}}

QTabBar::tab:selected {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_checked_light},
        stop: 1 {button_checked_dark}
    );
    
    border-bottom: none;
    
    height: 27px;
    
    color: black;
}}

QTabBar::tab:selected:hover {{
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 {button_checked_hover_light},
        stop: 1 {button_checked_hover_dark}
    );
    
    border-bottom: none;
    
    height: 27px;
    
    color: black;
}}

QTabBar::close-button {{
    image: url({close_icon_path});
    margin-right: 3px;
}}

QTabBar::close-button:hover {{
    background: {button_hover_2};
    border-radius: 5px;
    image: url({close_icon_path});
}}

""".format(
        **Colours[dark],
        down_icon_path=down_icon_path,
        close_icon_path=close_icon_path,
    )


class AmuletStyle(QProxyStyle):
    def __init__(self) -> None:
        super().__init__("fusion")
        self._style = QApplication.styleHints()
        self._style.colorSchemeChanged.connect(
            self._set_style_sheet, type=Qt.ConnectionType.QueuedConnection
        )
        enqueue(self._set_style_sheet)

    def _is_dark(self) -> bool:
        return self._style.colorScheme() == Qt.ColorScheme.Dark

    def _set_style_sheet(self) -> None:
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        app.setStyleSheet(get_style_sheet(self._is_dark()))

    def name(self, /) -> str:
        return "amulet"
