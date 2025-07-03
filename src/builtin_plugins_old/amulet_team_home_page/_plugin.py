from __future__ import annotations
import os

from PySide6.QtCore import QLocale, QCoreApplication

from amulet_editor.models.localisation import ATranslator
from amulet_editor.models.plugin import PluginV1

from amulet_team_level import get_level

import tablericons
import amulet_team_locale
from amulet_team_main_window import (
    register_widget,
    unregister_widget,
    register_layout,
    unregister_layout,
    WidgetConfig,
    WidgetStackConfig,
    WindowConfig,
    LayoutConfig,
    ButtonProxy,
    create_layout_button,
)

import amulet_team_home_page
from ._widget import HomeWidget

