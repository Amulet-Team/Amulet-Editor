from __future__ import annotations

from amulet_editor.data.project import get_level


from amulet_team_main_window.api import (
    register_view,
    unregister_view,
    get_active_window,
)

from amulet_team_3d_viewer._view_3d import HomeView


def load_plugin():
    if get_level() is not None:
        register_view(HomeView, "3d-cube-sphere.svg", "3D Editor")
        get_active_window().activate_view(HomeView)


def unload_plugin():
    unregister_view(HomeView)
