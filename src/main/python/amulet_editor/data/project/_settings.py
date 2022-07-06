import json
import os
from json import JSONDecodeError

from amulet_editor.data import project


def user_settings() -> dict:
    return {}


def project_settings() -> dict:
    if project.root() is None:
        return {}

    settings_file = os.path.join(project.root(), ".amulet", "settings.json")
    if not os.path.isfile(settings_file):
        settings = {}
    else:
        try:
            with open(settings_file, "r") as file:
                settings: dict = json.load(file)
        except JSONDecodeError:
            settings = {}

    return settings


def settings() -> dict:
    _settings = {}
    _settings.update(project_settings())
    return _settings
