from __future__ import annotations

from amulet_team_main_window.api import register_view

from .home import HomeView


def on_start():
    register_view("amulet_team:home", "home.svg", "Home", HomeView)
