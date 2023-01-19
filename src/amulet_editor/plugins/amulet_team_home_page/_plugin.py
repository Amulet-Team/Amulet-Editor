from __future__ import annotations

from amulet_team_main_window.api import (
    register_view,
    unregister_view,
    get_active_window,
)

from .home import HomeView


def on_start():
    register_view(HomeView, "home.svg", "Home")
    get_active_window().activate_view(HomeView)


def on_stop():
    unregister_view(HomeView)
