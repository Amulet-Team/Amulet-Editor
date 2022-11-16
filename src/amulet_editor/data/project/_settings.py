import json
import os

from amulet_editor.data import project

DefaultTheme = "Amulet Dark"


def default_settings() -> dict:
    return {
        "theme": DefaultTheme,
        "startup_size": [1400, 720],
    }


def user_settings() -> dict:
    return default_settings()


def project_settings() -> dict:
    if project.root() is None:
        return {}

    _settings_file = os.path.join(project.root(), ".amulet", "settings.json")
    if not os.path.exists(_settings_file):
        return {}

    return json.load(_settings_file)


def settings() -> dict:
    _settings = default_settings()
    _settings.update(project_settings())
    return _settings
