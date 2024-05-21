from __future__ import annotations

from amulet_editor.data.level import get_level
from amulet_editor.models.plugin import PluginV1
from amulet_team_main_window import ButtonProxy, create_layout_button


# from amulet_team_main_window.api import (
#     register_view,
#     unregister_view,
#     get_active_window,
# )
import tablericons

# from amulet_team_3d_viewer._view_3d import View3D

home_button: ButtonProxy | None = None
select_button: ButtonProxy | None = None


def _set_home_layout() -> None:
    pass
    # amulet_team_main_window.get_main_window().set_layout(HomeWidget)


def load_plugin() -> None:
    global home_button, select_button

    # Set up the home button
    # home_button = create_layout_button()
    # home_button.set_icon(tablericons.home)
    # home_button.set_name("Home")
    # home_button.set_callback(_set_home_layout)

    # if get_level() is None:
    #     # Make the home layout active by clicking the button
    #     home_button.click()
    # else:
    #     pass
    #     # register_view(View3D, tablericons.three_d_cube_sphere, "3D Editor")
    #     # get_active_window().activate_view(View3D)


def unload_plugin() -> None:
    pass
    # unregister_view(View3D)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
