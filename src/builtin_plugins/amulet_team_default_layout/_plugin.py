from __future__ import annotations

from amulet_editor.data.level import get_level
from amulet_editor.models.plugin import PluginV1
from amulet_team_main_window import (
    register_layout,
    unregister_layout,
    WidgetConfig,
    WidgetStackConfig,
    WindowConfig,
    LayoutConfig,
    ButtonProxy,
    create_layout_button,
)
from amulet_team_home_page import HomeWidget
from amulet_team_level_info import LevelInfoWidget

import tablericons

HomeLayoutID = "073bfd20-249e-4e0c-ad41-0bcb0c9db89f"
home_button: ButtonProxy | None = None
LevelInfoLayoutID = "4de0ebcd-f789-440f-9526-e6cc5d77caff"
level_info_button: ButtonProxy | None = None


def load_plugin() -> None:
    global home_button, level_info_button

    register_layout(
        HomeLayoutID,
        LayoutConfig(
            WindowConfig(
                None, None, WidgetStackConfig((WidgetConfig(HomeWidget.__qualname__),))
            ),
            (),
        ),
    )

    # Set up the home button
    home_button = create_layout_button(HomeLayoutID)
    home_button.set_icon(tablericons.home)
    home_button.set_name("Home")

    if get_level() is None:
        # Make the home layout active by clicking the button
        home_button.click()
    else:
        register_layout(
            LevelInfoLayoutID,
            LayoutConfig(
                WindowConfig(
                    None,
                    None,
                    WidgetStackConfig((WidgetConfig(LevelInfoWidget.__qualname__),)),
                ),
                (),
            ),
        )

        # Set up the home button
        level_info_button = create_layout_button(LevelInfoLayoutID)
        level_info_button.set_icon(tablericons.file_info)
        level_info_button.set_name("Level Info")
        level_info_button.click()
        # register_view(View3D, tablericons.three_d_cube_sphere, "3D Editor")
        # get_active_window().activate_view(View3D)


def unload_plugin() -> None:
    if home_button is not None:
        home_button.delete()
        unregister_layout(HomeLayoutID)
    if level_info_button is not None:
        level_info_button.delete()
        unregister_layout(LevelInfoLayoutID)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
