import json
import os

from amulet_editor.data import build


def get_public_settings() -> dict:
    if build.fbs_installed():
        from fbs_runtime import PUBLIC_SETTINGS

        return PUBLIC_SETTINGS

    else:
        settings_dir = os.path.join(os.getcwd(), "src", "build", "settings")

        with open(os.path.join(settings_dir, "base.json")) as json_file:
            base_settings: dict = json.load(json_file)

        public_settings = base_settings.get("public_settings", [])
        return {setting: base_settings[setting] for setting in public_settings}


PUBLIC_DATA = get_public_settings()
