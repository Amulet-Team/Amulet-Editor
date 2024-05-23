from __future__ import annotations

from amulet_editor.data.level import get_level
from amulet_editor.models.plugin import PluginV1
from amulet_team_main_window import register_layout, unregister_layout, WidgetConfig, WidgetStackConfig, WindowConfig, LayoutConfig, ButtonProxy, create_layout_button
from amulet_team_home_page import HomeWidget

import tablericons

HomeLayoutID = "073bfd20-249e-4e0c-ad41-0bcb0c9db89f"
home_button: ButtonProxy | None = None


def load_plugin() -> None:
    global home_button

    register_layout(HomeLayoutID, LayoutConfig(
        WindowConfig(
            None,
            None,
            WidgetStackConfig(
                (
                    WidgetConfig(HomeWidget.__qualname__),
                )
            )
        ),
        (),
    ))

    # Set up the home button
    home_button = create_layout_button(HomeLayoutID)
    home_button.set_icon(tablericons.home)
    home_button.set_name("Home")

    if get_level() is None:
        # Make the home layout active by clicking the button
        home_button.click()
    else:
        pass
        # register_view(View3D, tablericons.three_d_cube_sphere, "3D Editor")
        # get_active_window().activate_view(View3D)


def unload_plugin() -> None:
    if home_button is not None:
        home_button.delete()
    unregister_layout(HomeLayoutID)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
