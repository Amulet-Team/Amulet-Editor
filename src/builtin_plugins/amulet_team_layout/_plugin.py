from __future__ import annotations

from amulet_editor.data.level import get_level
from amulet_editor.models.plugin import PluginV1


# from amulet_team_main_window.api import (
#     register_view,
#     unregister_view,
#     get_active_window,
# )
import tablericons

# from amulet_team_3d_viewer._view_3d import View3D


def load_plugin() -> None:
    pass
    # if get_level() is not None:
    #     register_view(View3D, tablericons.three_d_cube_sphere, "3D Editor")
    #     get_active_window().activate_view(View3D)


def unload_plugin() -> None:
    pass
    # unregister_view(View3D)


plugin = PluginV1(load=load_plugin, unload=unload_plugin)
