import json
import os
import logging

from amulet_editor.data import project

log = logging.getLogger(__name__)


def default_settings() -> dict:
    return {
        "theme": "Amulet Dark",
        "startup_size": [1400, 720],
    }


def user_settings() -> dict:
    return default_settings()


def project_settings() -> dict:
    if project.root() is None:
        return {}

    _settings_file = os.path.join(project.root(), ".amulet", "settings.json")
    try:
        with open(_settings_file) as f:
            settings_ = json.load(f)
        if not isinstance(settings_, dict):
            raise TypeError(
                "Settings was not a dictionary. Reverting to default values."
            )
        return settings_
    except OSError:
        pass
    except (json.JSONDecodeError, TypeError) as e:
        log.exception(e)
    return {}


def settings() -> dict:
    _settings = default_settings()
    _settings.update(project_settings())
    return _settings
